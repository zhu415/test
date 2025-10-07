class VTBSDoc:
    def __init__(self, index, context):
        self.index = index
        self.context = context
        self.inputDoc, self.modelName, self.modelMktFwdName = self._readInputDoc()
        self.isExcessRF = self._isExcessReturnFwd()
        self.allCalFwdDates = []
        self.allCalFwdDatesNoBumps = []
        self.calVTBSDoc = None
        self.calVTBSDocNoSurfaceBumps = None
        self.calVTBSResultDoc = None
        self.calVTBSResultDocNoSurfaceBumps = None
        self.calMktFwdEle = None
        self.calMktFwdEleNoSurfaceBumps = None
        self.calMktFwdName = None
        self.calMktFwdNameNoBumps = None
        self.calMktFwdModelName = None
        self.calMktFwdModelNameNoBumps = None
        self.calMktFwdUnderlyingName = None
        self.strippedInputDoc = None
        self.bsElementBuilt = False  # Track if BS element has been built

    def _readInputDoc(self):
        xml = fetchInputDocAndValidate(self.index, self.context)
        modelName = getSingleRef(xml, './Calculate/Model').text
        modelMktFwdName = getSingleRef(xml, f'./Component/CalibratedForward/Name[text()="{modelName}"]/../MarketForward').text
        # MODIFIED: Don't call _buildBSElement here anymore
        return xml, modelName, modelMktFwdName

    def _isExcessReturnFwd(self):
        xml = self.inputDoc
        # Check if MarketForward is ExcessReturnForward
        forwardType = getSingleRef(xml, f'./Component/*/Name[text()="{self.modelMktFwdName}"]/..').tag
        return forwardType == "ExcessReturnForward"

    def _stripInputDoc(self):
        self.strippedInputDoc = deepcopy(self.inputDoc)
        calculate = getSingleRef(self.strippedInputDoc, './Calculate')
        self.strippedInputDoc.remove(calculate)
        return

    def _getFetchCalVTBSDoc(self):
        if self.calVTBSDoc is not None:
            return
        if self.strippedInputDoc is None:
            self._stripInputDoc()
        xml = deepcopy(self.strippedInputDoc)
        # Get DS
        dsStr = DSData.read_from_ds('Generic', f'VTBSParams/INDEX/{self.index}/null/null/null/null')
        pillarCutoff = None
        pillarCutoffStr = '' if pillarCutoff is None else f'<PillarCutOffDate>{pillarCutoff}</PillarCutOffDate>'
        if dsStr is None:
            vtbsElemStr = f"""
    <Component>
        <VolTargetBlackScholes>
            <CalibratedForward>{self.modelName}</CalibratedForward>{pillarCutoffStr}
            <Name>VolTargetBlackScholes_{self.index}</Name>
        </VolTargetBlackScholes>
    </Component>
"""
        else:
            dsList = dsStr.split('VTBSParams>')
            if len(dsList) != 3:
                raise Exception('Malformed DS')
            vtbsElemStr = f"""
<Component>
    <VolTargetBlackScholes>
        <CalibratedForward>{self.modelName}</CalibratedForward>{pillarCutoffStr}
        {dsList[1][:-2]}
        <Name>VolTargetBlackScholes_{self.index}</Name>
    </VolTargetBlackScholes>
</Component>
"""
        # Add VTBS object
        vtbsElem = ET.fromstring(vtbsElemStr)
        xml.append(vtbsElem)
        # Add FetchCalibratedVolTargetBlackScholes object
        fetchElemStr = f"""
<FetchCalibratedVolTargetBlackScholes>
    <VolTargetBlackScholes>VolTargetBlackScholes_{self.index}</VolTargetBlackScholes>
</FetchCalibratedVolTargetBlackScholes>
"""
        fetchElem = ET.fromstring(fetchElemStr)
        xml.append(fetchElem)
        self.calVTBSDoc = removeUnusedComponents(xml)
        return

    def _getFetchCalVTBSDocNoSurfaceBumps(self):
        if self.calVTBSDocNoSurfaceBumps is not None:
            return
        if self.calVTBSDoc is None:
            self._getFetchCalVTBSDoc()
        self.calVTBSDocNoSurfaceBumps = deepcopy(self.calVTBSDoc)
        for elem in self.calVTBSDocNoSurfaceBumps.xpath('.//VolTargetBlackScholes/CalibratedVolSurfaceOverhedge|.//VolTargetBlackScholes/GapFee'):
            elem.getparent().remove(elem)
        return

    def fetchCalVTBSDocToCalBSLibAMGObject(self, noBumps=False):
        if noBumps and (self.calVTBSDocNoSurfaceBumps is not None):
            return
        elif (not noBumps) and (self.calVTBSDoc is not None):
            return
        elif noBumps and (self.calVTBSDocNoSurfaceBumps is None):
            self._getFetchCalVTBSDocNoSurfaceBumps()
        if (not noBumps) and self.calVTBSDoc is None:
            self._getFetchCalVTBSDoc()
        if noBumps:
            vtbsDoc = self.calVTBSDocNoSurfaceBumps
        else:
            vtbsDoc = self.calVTBSDoc
        # Get raw calibrated surface (along with all the libamg objects it depends on)
        fetchCalVTBSResult = ET.fromstring(LibAMGUtilities.execute(ET.tostring(vtbsDoc, pretty_print=True).decode('utf-8')))
        fetchCalVTBSResult.tag = 'LibAMG'

        # The non-market forward part of the calibrated BS's forward is just for setting the spot
        # which we don't need to publish. The Java DIs also make the rest of this script more
        # complicated. Consequently, we set the forward to be the market forward and swap out the
        # DI for a dummy equity index of the same name. We also rename the YieldCurve to BorrowCost
        # Get the (calibrated) BlackScholes object and some forwards it depends on
        bs = getSingleRef(fetchCalVTBSResult, './BlackScholes')
        calFwdModelName = getSingleRef(bs, './Forward').text
        marketFwdName = getSingleRef(fetchCalVTBSResult, f'./Component/CalibratedForward/Name[text()="{calFwdModelName}"]/../MarketForward').text
        marketFwd = getSingleRef(fetchCalVTBSResult, f'./Component/*/Id[text()="{marketFwdName}"]|./Component/*/Name[text()="{marketFwdName}"]/..')
        if not noBumps:
            self.calMktFwdName = marketFwdName
            self.calMktFwdModelName = calFwdModelName
        else:
            self.calMktFwdNameNoBumps = marketFwdName
            self.calMktFwdModelNameNoBumps = calFwdModelName
        # Relabel the market forward's YieldCurve as BorrowCost
        yc = marketFwd.find('./YieldCurve')
        if yc is not None:
            yc.tag = 'BorrowCost'
        # Get underlier's info
        underlyingName = getSingleRef(marketFwd, './Underlying').text
        origUnderlying = getSingleRef(fetchCalVTBSResult, f'./Component/ScriptedJavaIndex/Name[text()="{underlyingName}"]/..')
        underlyingCurr = getSingleRef(origUnderlying, f'./Currency').text
        # Construct simple equity underlier to replace Java DI and perform the replacement
        newUnderlyingComponent = ET.Element('Component')
        newUnderlying = ET.SubElement(newUnderlyingComponent, 'EquityIndex')
        ET.SubElement(newUnderlying, 'Name').text = underlyingName
        ET.SubElement(newUnderlying, 'Currency').text = underlyingCurr

        origUnderlyingComponent = origUnderlying.getparent()
        origUnderlyingComponent.addnext(newUnderlyingComponent)
        origUnderlyingComponent.getparent().remove(origUnderlyingComponent)
        # Rename the calibrated BlackScholes and give it the forward we've been working on
        getSingleRef(bs, './Name').text = 'CalibratedBlackScholes'
        getSingleRef(bs, './Forward').text = marketFwdName
        # Set mutated fetchCalVTBSResult without extra components
        resultDoc = removeUnusedComponents(fetchCalVTBSResult)
        k = 0
        for elem in resultDoc.xpath('.//COGWA/CostOfGamma[text()="NaN"]/..'):
            elem.getparent().remove(elem)
            k += 1
        print(self.index, k)
        if noBumps:
            self.calVTBSResultDocNoSurfaceBumps = resultDoc
            self.calMktFwdEleNoSurfaceBumps = marketFwd
        else:
            self.calVTBSResultDoc = resultDoc
            self.calMktFwdEle = marketFwd
        self.calMktFwdUnderlyingName = underlyingName
        borrowCostRef = getSingleRef(marketFwd, "./BorrowCost")
        for yieldPt in borrowCostRef.iter("YieldPoint"):
            if not noBumps:
                self.allCalFwdDates.append(getSingleRef(yieldPt, './Date').text)
            else:
                self.allCalFwdDatesNoBumps.append(getSingleRef(yieldPt, './Date').text)
        return resultDoc

    def fetchCalVTBSResultsDoc(self):
        if self.calVTBSResultDoc is None:
            self.fetchCalVTBSDocToCalBSLibAMGObject(False)
        if self.calVTBSResultDocNoSurfaceBumps is None:
            self.fetchCalVTBSDocToCalBSLibAMGObject(True)
        
        # ADDED: Now that we have calibrated surfaces, build BS element if needed
        if not self.bsElementBuilt and self.inputDoc.find('.//BenchmarkBlackScholes') is not None:
            self._buildBSElement(self.inputDoc)
            self.bsElementBuilt = True
        
        return

    def _buildBSElement(self, xml):
        """Build BlackScholes element using calibrated VTBS surface"""
        if xml.find('.//BenchmarkBlackScholes') is None:
            return
        bbsComp = getSingleRef(xml, './/BenchmarkBlackScholes/..')
        bbs = getSingleRef(bbsComp, 'BenchmarkBlackScholes')
        bsComp = ET.Element('Component')
        bs = ET.SubElement(bsComp, 'BlackScholes')
        ET.SubElement(bs, 'Forward').text = getSingleRef(bbs, 'Forward').text
        
        # Use calibrated VTBS surface (Method 2)
        if self.calVTBSResultDoc is None:
            raise Exception('Cannot build BS element: calibrated surface not available yet')
        
        # Extract the calibrated volatility surface from the VTBS result
        calibratedBS = getSingleRef(self.calVTBSResultDoc, './BlackScholes')
        
        # Get the volatility surface component (COGWA or JVol)
        cogwaOrJVol = calibratedBS.find('./COGWA')
        if cogwaOrJVol is None:
            cogwaOrJVol = calibratedBS.find('./JVol')
            if cogwaOrJVol is None:
                raise Exception('Calibrated BlackScholes surface has neither COGWA nor JVol')
        
        # Copy the calibrated surface to our new BS element
        bs.append(deepcopy(cogwaOrJVol))
        
        # Copy other parameters from calibrated BS
        ET.SubElement(bs, 'Basis').text = getSingleRef(calibratedBS, './Basis').text
        ET.SubElement(bs, 'WeekendDayWeight').text = getSingleRef(calibratedBS, './WeekendDayWeight').text
        ET.SubElement(bs, 'HolidayWeight').text = getSingleRef(calibratedBS, './HolidayWeight').text
        ET.SubElement(bs, 'DayCount').text = getSingleRef(calibratedBS, './DayCount').text
        ET.SubElement(bs, 'TradingCalendar').text = getSingleRef(calibratedBS, './TradingCalendar').text
        ET.SubElement(bs, 'Direction').text = getSingleRef(calibratedBS, './Direction').text
        ET.SubElement(bs, 'DivTreatment').text = getSingleRef(calibratedBS, './DivTreatment').text
        ET.SubElement(bs, 'Name').text = getSingleRef(bbs, 'Name').text
        
        bbsComp.addnext(bsComp)
        bbsComp.getparent().remove(bbsComp)
