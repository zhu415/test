// First, add this method to the BenchmarkForward class to handle basis bumps
void BenchmarkForward::applyBasisBumpToShiftTermStructures(double basisBumpUsed)
{
if (Utils::isZero(basisBumpUsed))
return;

// We need to modify the shift term structures in the methodology
// Since the members are private, we'll need to create a modified copy
std::shared_ptr<BenchmarkForwardParameter::ForwardBenchmarkMethodology> modifiedMethodology(myForwardBenchmarkMethodology->clone());

// Apply basis bump to both borrow and dividend shift term structures if they exist
if (modifiedMethodology->myBorrowShiftTermStructure)
{
    modifiedMethodology->myBorrowShiftTermStructure = createBasisBumpedShiftTermStructure(
        modifiedMethodology->myBorrowShiftTermStructure, basisBumpUsed);
}

if (modifiedMethodology->myDividendShiftTermStructure)
{
    modifiedMethodology->myDividendShiftTermStructure = createBasisBumpedShiftTermStructure(
        modifiedMethodology->myDividendShiftTermStructure, basisBumpUsed);
}

// Replace the methodology with the modified one
myForwardBenchmarkMethodology = modifiedMethodology;

}

// Helper method to create a basis-bumped version of ShiftTermStructure
std::shared_ptr<const BenchmarkForwardParameter::ShiftTermStructure>
BenchmarkForward::createBasisBumpedShiftTermStructure(
const std::shared_ptr<const BenchmarkForwardParameter::ShiftTermStructure>& original,
double basisBump) const
{
if (!original)
return nullptr;

// Create a description document to clone the original structure
Description::Document cloneDoc;
cloneDoc.setMode(Description::Document::WRITE);

// Describe the original to capture its state
BenchmarkForwardParameter::ShiftTermStructure* mutableOriginal = 
    const_cast<BenchmarkForwardParameter::ShiftTermStructure*>(original.get());
BenchmarkForwardParameter::ShiftTermStructure::describe(mutableOriginal, cloneDoc);

// Switch to read mode to create new instance
cloneDoc.setMode(Description::Document::READ);

// Create new instance from the description
auto basisBumpedShiftTS = std::make_shared<BenchmarkForwardParameter::ShiftTermStructure>(cloneDoc);

// Now we need to modify the values - since myValues is private, we'll use a friend approach
// or add a public method to ShiftTermStructure to apply basis bumps
basisBumpedShiftTS->applyBasisBump(basisBump);

return basisBumpedShiftTS;


}

// Modified init method to handle basis bumps
void BenchmarkForward::init(const BenchmarkForward::InitMode initMode,
const BenchmarkForward::WriteBenchmarkForwardOut writeBenchmarkForwardOut,
double basisBumpUsed)
{
if (!myForwardBenchmarkMethodology)
AMG_THROW(“A ForwardBenchmarkMethodology should be provided”);


const std::shared_ptr<const Indices::IndexBase>& destination = getUnderlying();
AMG_REQUIRE(destination, "The destination underlier needs to be provided.");
myForwardBenchmarkMethodology->checkSourceCompatibility(destination, mySources);

// Apply basis bump to shift term structures if needed
if (!Utils::isZero(basisBumpUsed))
{
    applyBasisBumpToShiftTermStructures(basisBumpUsed);
}

if (initMode == BenchmarkForward::InitMode::WITHOUT_RECALIBRATION) // Only called in the init from the describe
{
    if (myBenchmarkForwardOut != nullptr)
    {
        myBenchmarkForward = myBenchmarkForwardOut;
        ForwardBase::init(myBenchmarkForward->getFundingAndProjection(), &destination);
        return;
    }
    else
    {
        // How does this work if myBenchmarkForwardOut is provided
        myBenchmarkForward = std::make_shared<const Forward>(
            getInitialSpot(),
            destination,
            getFundingAndProjection(),
            nullptr /*dividends - will be calibrated in buildBenchmarkForwardData*/,
            nullptr /*borrowCost - will be calibrated in buildBenchmarkForwardData*/);
    }
}

// First calibrate the spot and the curves. This is always done, even if we are under partial decomposition
calibrateSpot(destination, mySourceModelBase, myBenchmarkForward);
myForwardBenchmarkMethodology->setFundingAndProjection(destination, mySources, mySourceModelBase, getFundingAndProjection(), myBenchmarkForward);
Models::FundingAndProjection fundingAndProjection = myBenchmarkForward->getFundingAndProjection();
ForwardBase::init(fundingAndProjection, &destination);

if (initMode != BenchmarkForward::InitMode::SPOT_AND_PROJECTION_ONLY) { // Recalibrate Borrow and dividends
    // Pass the basisBumpUsed to buildBenchmarkForwardData
    myForwardBenchmarkMethodology->buildBenchmarkForwardData(destination, mySources, mySourceModelBase, myMarkedDividends, myDecrement, myBenchmarkForward, basisBumpUsed);
}

if (writeBenchmarkForwardOut == BenchmarkForward::WriteBenchmarkForwardOut::DO_WRITE_OUT && myBenchmarkForward)
    myBenchmarkForwardOut = myBenchmarkForward;
```

}

// Overloaded version to maintain backward compatibility
void BenchmarkForward::init(const BenchmarkForward::InitMode initMode,
const BenchmarkForward::WriteBenchmarkForwardOut writeBenchmarkForwardOut)
{
init(initMode, writeBenchmarkForwardOut, 0.0); // Default basisBumpUsed = 0.0
}

// Updated bumpedCloneFullDecomposition method
ForwardBase* BenchmarkForward::bumpedCloneFullDecomposition(Risk::BumpFetcher& bumpFetcher, double& bumpUsed, ModelBumpCache& bumpCache, const double multiple) const
{
bumpUsed = 1.0e-3; // change this value for basis risk checking
const Risk::BumpBase& bump = *bumpFetcher.deprecatedGet();
Utils::CopyOnWrite<BenchmarkForward> copy(this);
copy.reset(ForwardBase::bumpedClone(bumpFetcher, bumpUsed, bumpCache, multiple));

```
if (isProxyRisk(bump))
{
    if (Utils::isNaN(bumpUsed))
        bumpUsed = 0.0;
    return copy.release();
}

const char* bumpClassTag = bump.classTag();

if (bumpClassTag == Risk::BumpSpot::ourClassTag)
{
    bumpWithRecalibration(bumpFetcher, bumpUsed, bumpCache, multiple, copy, BenchmarkForward::RevertToUnbumpedStateMode::DO_NOT_REVERT, BenchmarkForward::WriteBenchmarkForwardOut::DO_WRITE_OUT);
}
else if (bumpClassTag == Risk::BumpBasis::ourClassTag)
{
    const std::shared_ptr<const Indices::IndexBase>& destination = getUnderlying();
    
    // Extract the actual bump size from the BumpBasis object
    const Risk::BumpBasis& bumpBasis = static_cast<const Risk::BumpBasis&>(bump);
    double basisBumpAmount = bumpBasis.getBumpAmount() * multiple; // Adjust method name as needed
    bumpUsed = basisBumpAmount;
    
    // Re-initialize with basis bump applied
    copy->init(BenchmarkForward::InitMode::WITHOUT_RECALIBRATION, 
              BenchmarkForward::WriteBenchmarkForwardOut::DO_NOT_WRITE_OUT,
              basisBumpAmount);
}
else
{
    const BenchmarkForward::WriteBenchmarkForwardOut writeBenchmarkForwardOut = 
        bump.matchClassTag(Risk::BumpArbitrageTolerance::ourClassTag) ?
        BenchmarkForward::WriteBenchmarkForwardOut::DO_WRITE_OUT : 
        BenchmarkForward::WriteBenchmarkForwardOut::DO_NOT_WRITE_OUT;
        
    bumpWithRecalibration(bumpFetcher, bumpUsed, bumpCache, multiple, copy, 
                        BenchmarkForward::RevertToUnbumpedStateMode::DO_NOT_REVERT, 
                        writeBenchmarkForwardOut);
}

applyDecrementSpotBump(bump, copy);
return copy.release();
```

}

// Add this method to the ShiftTermStructure class (in the .cpp file)
void ShiftTermStructure::applyBasisBump(double basisBump)
{
if (Utils::isZero(basisBump))
return;

```
// Apply the basis bump to all values
for (size_t i = 0; i < myValues.size(); ++i)
{
    if (myShiftTermStructureMethod == BenchmarkParameterEnums::ADDITIVE)
    {
        myValues[i] += basisBump;
    }
    else if (myShiftTermStructureMethod == BenchmarkParameterEnums::MULTIPLICATIVE)
    {
        myValues[i] *= (1.0 + basisBump);
    }
}

// Re-initialize the interpolator with the updated values
if (myModelDate)
{
    init();
}


}

// And add this declaration to the ShiftTermStructure class in the header file (.hpp):
// In the public section of ShiftTermStructure class:
void applyBasisBump(double basisBump);

// Add these method declarations to the private section of BenchmarkForward class in the .hpp file:

private:
// … existing private members …


// New methods for basis bump support
void init(const BenchmarkForward::InitMode initMode, 
         const BenchmarkForward::WriteBenchmarkForwardOut writeBenchmarkForwardOut,
         double basisBumpUsed);
         
void applyBasisBumpToShiftTermStructures(double basisBumpUsed);

std::shared_ptr<const BenchmarkForwardParameter::ShiftTermStructure> 
createBasisBumpedShiftTermStructure(
    const std::shared_ptr<const BenchmarkForwardParameter::ShiftTermStructure>& original, 
    double basisBump) const;


// Also, you’ll need to make myBorrowShiftTermStructure and myDividendShiftTermStructure
// accessible. You have a few options:

// Option 1: Add friend declaration to ForwardBenchmarkMethodology
friend class BenchmarkForward;

// Option 2: Add protected getter/setter methods to ForwardBenchmarkMethodology:
protected:
std::shared_ptr<BenchmarkForwardParameter::ShiftTermStructure> getBorrowShiftTermStructure() const
{
return std::const_pointer_cast<BenchmarkForwardParameter::ShiftTermStructure>(myBorrowShiftTermStructure);
}

```
std::shared_ptr<BenchmarkForwardParameter::ShiftTermStructure> getDividendShiftTermStructure() const 
{ 
    return std::const_pointer_cast<BenchmarkForwardParameter::ShiftTermStructure>(myDividendShiftTermStructure); 
}

void setBorrowShiftTermStructure(std::shared_ptr<const BenchmarkForwardParameter::ShiftTermStructure> shiftTS)
{
    myBorrowShiftTermStructure = shiftTS;
}

void setDividendShiftTermStructure(std::shared_ptr<const BenchmarkForwardParameter::ShiftTermStructure> shiftTS)
{
    myDividendShiftTermStructure = shiftTS;
}
