// Add these fields to your class
@AMGSerialise(Order = 220, Default = "90")
private int myVolatilityWindow;

@AMGSerialise(Order = 221, Default = "0.001")
private double myWeightMatchingTolerance;

// Add this method to calculate inverse volatility weights
private Map<String, Double> calculateInverseVolWeights(
        RebalanceContext context, 
        ???Date currentDate,
        double equityMultiplier,
        double rateMultiplier) throws AMGException {
    
    Map<String, Double> invVolWeights = new HashMap<>();
    double totalInverseVol = 0.0;
    
    // For each identifier, we need to get volatility
    // This is the challenge - we need 90 days of price history
    // library might provide this through context.getPriceContext()
    
    for (Identifier id : myIdentifier) {
        String marketId = id.getMarketId();
        
        // Skip cash positions
        if (marketId.contains(".CASH")) {
            continue;
        }
        
        // Determine asset class and multiplier
        double multiplier = 1.0;
        if (marketId.contains("spxeralt")) { // equity
            multiplier = equityMultiplier;
        } else if (marketId.contains("spusttp")) { // rate
            multiplier = rateMultiplier;
        }
        // other assets get multiplier = 1.0
        
        // Calculate volatility (this is simplified - you need 90-day history)
        double volatility = calculateVolatility(context, marketId, currentDate);
        
        if (volatility > 0) {
            double inverseVol = (1.0 / volatility) / multiplier;
            invVolWeights.put(marketId, inverseVol);
            totalInverseVol += inverseVol;
        }
    }
    
    // Normalize weights
    for (Map.Entry<String, Double> entry : invVolWeights.entrySet()) {
        entry.setValue(entry.getValue() / totalInverseVol);
    }
    
    return invVolWeights;
}

// Simplified volatility calculation (you need to implement proper 90-day rolling window)
private double calculateVolatility(RebalanceContext context, String marketId, ???Date endDate) {
    // This is where you'd need to access 90 days of price history
    // The challenge is that Library might not provide this easily
    
    // Placeholder - you'd need to implement actual calculation
    return 0.15; // Default 15% volatility
}

// Method to find best matching volatility scenario
private String findBestVolScenario(Map<String, Double> actualWeights) throws AMGException {
    
    // Normalize actual weights (excluding cash)
    Map<String, Double> normalizedActual = new HashMap<>();
    double totalNonCash = 0.0;
    for (Map.Entry<String, Double> entry : actualWeights.entrySet()) {
        if (!entry.getKey().contains(".CASH")) {
            totalNonCash += entry.getValue();
        }
    }
    for (Map.Entry<String, Double> entry : actualWeights.entrySet()) {
        if (!entry.getKey().contains(".CASH")) {
            normalizedActual.put(entry.getKey(), entry.getValue() / totalNonCash);
        }
    }
    
    // Test four scenarios
    double[][] multipliers = {{1, 1}, {1, 10}, {5, 1}, {5, 10}};
    String[] scenarios = {"a", "b", "c", "d"};
    
    String bestScenario = "a";
    double minDistance = Double.MAX_VALUE;
    
    for (int i = 0; i < multipliers.length; i++) {
        Map<String, Double> invVolWeights = calculateInverseVolWeights(
            null, // need context
            null, // need date
            multipliers[i][0], 
            multipliers[i][1]
        );
        
        // Calculate distance between actual and calculated weights
        double distance = 0.0;
        for (Map.Entry<String, Double> entry : normalizedActual.entrySet()) {
            Double calcWeight = invVolWeights.get(entry.getKey());
            if (calcWeight != null) {
                distance += Math.pow(entry.getValue() - calcWeight, 2);
            }
        }
        distance = Math.sqrt(distance);
        
        if (distance < minDistance) {
            minDistance = distance;
            bestScenario = scenarios[i];
        }
    }
    
    return bestScenario;
}

// Modified publishExtraOutputs to include scenario detection
public void publishExtraOutputs(ExtraOutputCollector extraOutputsCollector, 
        PortfolioContextRepository portfolioRepository, 
        IndexSpecificDailyResult todaysDailyResult) throws AMGException {
    
    // Debug output
    System.out.println("========== VOLATILITY SCENARIO DETECTION ==========");
    
    if (myThirdPartyIndexComps != null) {
        String scenario = findBestVolScenario(myThirdPartyIndexComps);
        System.out.println("Best matching scenario: " + scenario);
        
        // If scenario is "d" (5,10), apply 0.75 scaling
        if ("d".equals(scenario)) {
            System.out.println("Applying 0.75 scaling for scenario D");
            // You would need to apply this scaling to the weights
            // This might require modifying the weights before they're used
        }
        
        // Output to extra outputs
        extraOutputsCollector.value(Publish, 
            ExtraOutputs.key("VOLATILITY_SCENARIO", "scenario"), 
            scenario);
    }
    
    // Rest of existing code...
}



// Option 2: Use  historical data access: if provides historical price access, you'd need to:


// In rebalanceInit, request historical data
for (int i = -90; i < 0; i++) {
    ???Date histDate = rebalanceCalendar.addBusinessDays(initContext.getBuildDate(), i);
    // Request fixing for this date
    initContext.getPropertyManager().addFixingRequirement(index, source, histDate);
}
