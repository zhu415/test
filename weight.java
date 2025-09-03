// Add these methods to the D_ExternalIndexWeightVolTarget class

// New member variables to add at the class level
@AMGSerialise(Order = 220, Default = "0.1")
private double myTargetVolatility = 0.1; // 10% default target volatility

@AMGSerialise(Order = 221)
private Map<String, Double> myPreviousVolatilities; // 90-day vols up to t-3

// Volatility multiplier combinations
private static final double[][] MULTIPLIER_COMBINATIONS = {
    {1.0, 1.0},   // Equity: 1, Rate: 1
    {1.0, 10.0},  // Equity: 1, Rate: 10
    {5.0, 1.0},   // Equity: 5, Rate: 1
    {5.0, 10.0}   // Equity: 5, Rate: 10
};

// Helper method to identify component type
private String getComponentType(String marketId) {
    if (marketId.contains(".CASH")) {
        return "CASH";
    } else if (marketId.contains("EQUITY") || marketId.contains("EQ")) {
        return "EQUITY";
    } else if (marketId.contains("RATE") || marketId.contains("BOND")) {
        return "RATE";
    } else {
        return "OTHER";
    }
}

// Method to fetch historical price from FixingTable
private double getHistoricalPrice(RebalanceContext context, String marketId, LibAMGDate date) throws AMGException {
    try {
        final ProductUniverse universe = context.getUniverse();
        final PortfolioProduct product = universe.findProduct(marketId);
        if (product != null) {
            final Index spotIndex = product.getPriceDependency(PriceTypeEnum.Spot.name())
                .getIndex(context.getIndexRetriever());
            return context.getPriceContext().value(spotIndex, date);
        }
    } catch (Exception e) {
        throw new AMGException("Failed to fetch historical price for " + marketId + " on " + date, e);
    }
    return Double.NaN;
}

// Calculate 91-day volatility from 90-day volatility and new return
private double calculate91DayVolatility(double vol90, double newReturn) {
    double var90 = vol90 * vol90;
    double var91 = (89.0 * var90 + newReturn * newReturn) / 90.0;
    return Math.sqrt(var91);
}

// Calculate weights using inverse volatility
private Map<String, Double> calculateInverseVolWeights(Map<String, Double> volatilities, 
                                                        Map<String, Double> multipliers) {
    Map<String, Double> inverseVols = new HashMap<>();
    double sumInverse = 0.0;
    
    for (Map.Entry<String, Double> entry : volatilities.entrySet()) {
        String component = entry.getKey();
        double vol = entry.getValue();
        double multiplier = multipliers.getOrDefault(component, 0.0);
        
        if (multiplier > 0 && vol > 0) {
            double inverse = myTargetVolatility / (vol * multiplier);
            inverseVols.put(component, inverse);
            sumInverse += inverse;
        } else {
            inverseVols.put(component, 0.0);
        }
    }
    
    Map<String, Double> weights = new HashMap<>();
    if (sumInverse > 0) {
        for (Map.Entry<String, Double> entry : inverseVols.entrySet()) {
            weights.put(entry.getKey(), entry.getValue() / sumInverse);
        }
    }
    
    return weights;
}

// Main method to identify volatility multiplier combination
public void identifyVolatilityMultipliers(TodayManager todayManager, RebalanceContext context,
                                         DailyResults yesterdaysResult,
                                         IndexSpecificDailyResult todaysResult) throws AMGException {
    
    LibAMGDate valDate = todayManager.getValDate();
    Calendar evolutionCalendar = todayManager.getEvolutionCalendar();
    
    // Get dates
    LibAMGDate tMinus2 = evolutionCalendar.addBusinessDays(valDate, -2);
    LibAMGDate tMinus3 = evolutionCalendar.addBusinessDays(valDate, -3);
    
    // Get target volatility from existing method
    double targetVol = getTargetVol();
    
    System.out.println("\n=== Volatility Multiplier Identification ===");
    System.out.println("Current Date (t): " + valDate);
    System.out.println("t-2: " + tMinus2);
    System.out.println("t-3: " + tMinus3);
    System.out.println("Target Volatility: " + targetVol);
    
    // Step 1: Calculate 91-day volatilities up to t-2
    Map<String, Double> volatilities91Day = new HashMap<>();
    
    for (int i = 0; i < myIdentifier.size(); i++) {
        String marketId = myIdentifier.get(i).getMarketId();
        String componentType = getComponentType(marketId);
        
        if (!"CASH".equals(componentType)) {
            // Get 90-day volatility up to t-3 (from external source or previous calculation)
            double vol90 = myPreviousVolatilities != null ? 
                          myPreviousVolatilities.getOrDefault(marketId, 0.05) : 0.05; // Default 5%
            
            // Get prices at t-2 and t-3
            double priceT2 = getHistoricalPrice(context, marketId, tMinus2);
            double priceT3 = getHistoricalPrice(context, marketId, tMinus3);
            
            // Calculate return at t-2
            double returnT2 = (priceT2 / priceT3) - 1.0;
            
            // Calculate 91-day volatility
            double vol91 = calculate91DayVolatility(vol90, returnT2);
            volatilities91Day.put(componentType, vol91);
            
            System.out.println(String.format("%s: 90-day vol=%.4f, return(t-2)=%.4f, 91-day vol=%.4f",
                             componentType, vol90, returnT2, vol91));
        }
    }
    
    // Step 2: Get actual weights from today's results (normalize non-cash weights)
    Map<String, Double> actualWeights = new HashMap<>();
    double sumNonCashWeights = 0.0;
    
    for (int i = 0; i < myIdentifier.size(); i++) {
        String marketId = myIdentifier.get(i).getMarketId();
        String componentType = getComponentType(marketId);
        double weight = todaysResult.myWeights[i];
        
        if (!"CASH".equals(componentType)) {
            actualWeights.put(componentType, weight);
            sumNonCashWeights += weight;
        }
    }
    
    // Normalize actual weights
    if (sumNonCashWeights > 0) {
        for (Map.Entry<String, Double> entry : actualWeights.entrySet()) {
            entry.setValue(entry.getValue() / sumNonCashWeights);
        }
    }
    
    System.out.println("\nNormalized actual weights: " + actualWeights);
    
    // Step 3: Test each multiplier combination
    double minDistance = Double.MAX_VALUE;
    int bestCombinationIdx = -1;
    Map<String, Double> bestWeights = null;
    
    System.out.println("\n=== Testing Multiplier Combinations ===");
    
    for (int idx = 0; idx < MULTIPLIER_COMBINATIONS.length; idx++) {
        double equityMultiplier = MULTIPLIER_COMBINATIONS[idx][0];
        double rateMultiplier = MULTIPLIER_COMBINATIONS[idx][1];
        
        Map<String, Double> multipliers = new HashMap<>();
        multipliers.put("EQUITY", equityMultiplier);
        multipliers.put("RATE", rateMultiplier);
        multipliers.put("OTHER", volatilities91Day.containsKey("OTHER") ? 1.0 : 0.0);
        
        // Calculate weights for this combination
        Map<String, Double> calculatedWeights = calculateInverseVolWeights(volatilities91Day, multipliers);
        
        // Calculate distance
        double distance = 0.0;
        for (String component : actualWeights.keySet()) {
            double actual = actualWeights.getOrDefault(component, 0.0);
            double calculated = calculatedWeights.getOrDefault(component, 0.0);
            distance += Math.abs(actual - calculated);
        }
        
        System.out.println(String.format("Combination %d (Equity:%.0f, Rate:%.0f): distance=%.6f",
                         idx, equityMultiplier, rateMultiplier, distance));
        System.out.println("  Calculated weights: " + calculatedWeights);
        
        if (distance < minDistance) {
            minDistance = distance;
            bestCombinationIdx = idx;
            bestWeights = new HashMap<>(calculatedWeights);
        }
    }
    
    // Step 4: Report results
    System.out.println("\n=== RESULTS ===");
    System.out.println(String.format("Best match: Combination %d (Equity:%.0f, Rate:%.0f)",
                     bestCombinationIdx,
                     MULTIPLIER_COMBINATIONS[bestCombinationIdx][0],
                     MULTIPLIER_COMBINATIONS[bestCombinationIdx][1]));
    System.out.println("Minimum distance: " + minDistance);
    System.out.println("Best calculated weights: " + bestWeights);
    
    // Step 5: Check for special case (Equity:5, Rate:10) and adjust weights
    if (MULTIPLIER_COMBINATIONS[bestCombinationIdx][0] == 5.0 && 
        MULTIPLIER_COMBINATIONS[bestCombinationIdx][1] == 10.0) {
        
        System.out.println("\n*** IMPORTANT FLAG: Equity:5, Rate:10 combination detected! ***");
        System.out.println("\nAdjusting today's weights by dividing by 0.75:");
        
        System.out.println("\nWeights BEFORE adjustment:");
        for (int i = 0; i < myIdentifier.size(); i++) {
            String marketId = myIdentifier.get(i).getMarketId();
            System.out.println(String.format("  %s: %.6f", marketId, todaysResult.myWeights[i]));
        }
        
        // Adjust weights
        for (int i = 0; i < todaysResult.myWeights.length; i++) {
            todaysResult.myWeights[i] = todaysResult.myWeights[i] / 0.75;
        }
        
        System.out.println("\nWeights AFTER adjustment:");
        for (int i = 0; i < myIdentifier.size(); i++) {
            String marketId = myIdentifier.get(i).getMarketId();
            System.out.println(String.format("  %s: %.6f", marketId, todaysResult.myWeights[i]));
        }
    }
    
    System.out.println("\n=== End Volatility Multiplier Identification ===\n");
}

// Method to integrate into the rebalance process
private void performVolatilityMultiplierAnalysis(TodayManager todayManager, 
                                                 RebalanceContext context,
                                                 DailyResults yesterdaysResult,
                                                 IndexSpecificDailyResult todaysResult) {
    try {
        // Initialize previous volatilities if needed (this would typically come from external data)
        if (myPreviousVolatilities == null) {
            myPreviousVolatilities = new HashMap<>();
            // These would be populated from external source in practice
            // Using placeholder values for demonstration
            for (Identifier id : myIdentifier) {
                myPreviousVolatilities.put(id.getMarketId(), 0.05); // 5% default
            }
        }
        
        // Run the volatility multiplier identification
        identifyVolatilityMultipliers(todayManager, context, yesterdaysResult, todaysResult);
        
    } catch (Exception e) {
        System.err.println("Error in volatility multiplier analysis: " + e.getMessage());
        e.printStackTrace();
    }
}
