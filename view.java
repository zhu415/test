private Map<String, Double> getThirdPartyIndexWeights(LibAMGDate buildDate, Calendar cal, 
        IndexSource indexProvider, String myIndex, List<Identifier> myIdentifier) throws AMGException {
    
    LibAMGDate prevDate = cal.addBusinessDays(buildDate, -myWeightsLag);
    final GenericDataResponse thirdPartyCompsGenericData = GenericDataRequestUtils.fetchGenericDataResponse(
            indexProvider, prevDate, prevDate, "ThirdPartyIndexComps", 
            Arrays.asList(new QueryParameter[] {new QueryParameter("index", myIndex)}));
    
    if (thirdPartyCompsGenericData == null || thirdPartyCompsGenericData.size() == 0)
        throw new AMGException("missing composition data on " + prevDate);
    
    // ============ DEBUG SECTION START ============
    System.out.println("\n========================================");
    System.out.println("=== Third Party Index Weights Debug ===");
    System.out.println("========================================");
    System.out.println("Index: " + myIndex);
    System.out.println("Date: " + prevDate);
    System.out.println("Data size: " + thirdPartyCompsGenericData.size() + " entries\n");
    
    // 1. Explore all available methods using reflection
    System.out.println("=== Available Methods ===");
    Method[] methods = thirdPartyCompsGenericData.getClass().getMethods();
    for (Method method : methods) {
        if (method.getName().startsWith("get") && method.getParameterCount() <= 2) {
            System.out.println("  Method: " + method.getName() + 
                             " (params: " + method.getParameterCount() + 
                             ", returns: " + method.getReturnType().getSimpleName() + ")");
        }
    }
    
    // 2. Explore all declared fields
    System.out.println("\n=== Available Fields ===");
    Field[] fields = thirdPartyCompsGenericData.getClass().getDeclaredFields();
    for (Field field : fields) {
        System.out.println("  Field: " + field.getName() + " (type: " + field.getType().getSimpleName() + ")");
    }
    
    // 3. Try to discover column names
    System.out.println("\n=== Attempting to Find Column Names ===");
    try {
        // Try common method names for getting column information
        String[] methodsToTry = {"getColumnNames", "getColumns", "getFieldNames", "getHeaders", "getKeys"};
        for (String methodName : methodsToTry) {
            try {
                Method method = thirdPartyCompsGenericData.getClass().getMethod(methodName);
                Object result = method.invoke(thirdPartyCompsGenericData);
                System.out.println("  Found " + methodName + "(): " + result);
            } catch (Exception e) {
                // Method doesn't exist, continue
            }
        }
    } catch (Exception e) {
        System.out.println("  Could not retrieve column names automatically");
    }
    
    // 4. Try common field names to see what data is available
    System.out.println("\n=== Probing for Available Data Fields ===");
    String[] possibleFields = {
        "constituentId", "weight", "name", "description", "sector", "industry",
        "country", "currency", "shares", "marketCap", "price", "return",
        "cusip", "isin", "sedol", "ticker", "exchange", "assetClass",
        "notional", "percentWeight", "rank", "date", "updateDate"
    };
    
    if (thirdPartyCompsGenericData.size() > 0) {
        System.out.println("  Testing fields on first row:");
        for (String fieldName : possibleFields) {
            try {
                String strValue = thirdPartyCompsGenericData.getStr(fieldName, 0);
                System.out.println("    ✓ " + fieldName + " (String): \"" + strValue + "\"");
            } catch (Exception e1) {
                try {
                    double dblValue = thirdPartyCompsGenericData.getDouble(fieldName, 0);
                    System.out.println("    ✓ " + fieldName + " (Double): " + dblValue);
                } catch (Exception e2) {
                    // Field doesn't exist or is another type
                }
            }
        }
    }
    
    // 5. Print the toString() representation
    System.out.println("\n=== Object toString() Output ===");
    System.out.println(thirdPartyCompsGenericData.toString());
    
    // 6. Print detailed information for each row
    System.out.println("\n=== Detailed Data for All Rows ===");
    double totalWeight = 0.0;
    
    // ============ ORIGINAL LOGIC WITH DEBUG ============
    Map<String, String> bbgToMarketIdMap = myIdentifier.stream()
            .collect(Collectors.toMap(Identifier::getBbgId, Identifier::getMarketId));
    myThirdPartyIndexComps = myIdentifier.stream()
            .collect(Collectors.toMap(Identifier::getMarketId, 
                    x -> myFallBackToZeroWeight ? 0.0 : Double.NaN));
    
    for (int i = 0; i < thirdPartyCompsGenericData.size(); i++) {
        double weight = thirdPartyCompsGenericData.getDouble("weight", i);
        String ticker = thirdPartyCompsGenericData.getStr("constituentId", i);
        
        // Debug print for each entry
        System.out.println("Row " + i + ":");
        System.out.println("  constituentId: " + ticker);
        System.out.println("  weight: " + weight + " (" + String.format("%.4f%%", weight * 100) + ")");
        
        // Try to get additional fields for this row
        try {
            String name = thirdPartyCompsGenericData.getStr("name", i);
            System.out.println("  name: " + name);
        } catch (Exception e) { /* field doesn't exist */ }
        
        try {
            String sector = thirdPartyCompsGenericData.getStr("sector", i);
            System.out.println("  sector: " + sector);
        } catch (Exception e) { /* field doesn't exist */ }
        
        try {
            double shares = thirdPartyCompsGenericData.getDouble("shares", i);
            System.out.println("  shares: " + shares);
        } catch (Exception e) { /* field doesn't exist */ }
        
        try {
            double marketCap = thirdPartyCompsGenericData.getDouble("marketCap", i);
            System.out.println("  marketCap: " + marketCap);
        } catch (Exception e) { /* field doesn't exist */ }
        
        totalWeight += weight;
        
        // Original logic
        if (myIndexToBeReset != null && ticker.equals(myIndexToBeReset))
            myResetIndexPrices.put(myIndexToBeReset, weight);
        if (bbgToMarketIdMap.get(ticker) != null)
            myThirdPartyIndexComps.put(bbgToMarketIdMap.get(ticker), weight);
    }
    
    // 7. Print summary statistics
    System.out.println("\n=== Summary Statistics ===");
    System.out.println("Total entries processed: " + thirdPartyCompsGenericData.size());
    System.out.println("Total weight sum: " + totalWeight + " (" + String.format("%.6f", totalWeight) + ")");
    System.out.println("Weight difference from 1.0: " + String.format("%.10f", Math.abs(totalWeight - 1.0)));
    System.out.println("Number of matched identifiers: " + 
                      myThirdPartyIndexComps.entrySet().stream()
                          .filter(e -> !Double.isNaN(e.getValue()) && e.getValue() != 0.0)
                          .count());
    System.out.println("Number of unmatched identifiers: " + 
                      myThirdPartyIndexComps.entrySet().stream()
                          .filter(e -> Double.isNaN(e.getValue()) || e.getValue() == 0.0)
                          .count());
    
    // 8. Print the final mapping
    System.out.println("\n=== Final Mapping (Market ID -> Weight) ===");
    myThirdPartyIndexComps.entrySet().stream()
        .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
        .forEach(entry -> {
            System.out.println("  " + entry.getKey() + " -> " + 
                             entry.getValue() + " (" + 
                             String.format("%.4f%%", entry.getValue() * 100) + ")");
        });
    
    System.out.println("\n========================================");
    System.out.println("=== End of Debug Information ===");
    System.out.println("========================================\n");
    // ============ DEBUG SECTION END ============
    
    // Original validation logic
    if ((myIndexToBeReset != null && myIndexToBeReset.length() != 0) && 
            (myResetIndexPrices == null || myResetIndexPrices.size() == 0))
        throw new RuntimeException("Missing price of " + myIndexToBeReset);
    
    if (myThirdPartyIndexComps.entrySet().stream().anyMatch(x -> Double.isNaN(x.getValue())))
        throw new RuntimeException("missing weight!!");
    
    if (myCheckTotalWeight && (Math.abs(myThirdPartyIndexComps.entrySet().stream()
            .mapToDouble(Map.Entry::getValue).sum() - 1.0) > myTotalWeightTolerance))
        throw new RuntimeException("total weight not equal to 1!!");
    
    return myThirdPartyIndexComps;
}
