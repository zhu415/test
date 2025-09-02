public void publishExtraOutputs(ExtraOutputCollector extraOutputsCollector, 
        PortfolioContextRepository portfolioRepository, 
        IndexSpecificDailyResult todaysDailyResult) throws AMGException {
    
    // Simple debug test first
    try {
        java.io.FileWriter fw = new java.io.FileWriter("C:\\Users\\xiazhu\\Desktop\\PUBLISH_TEST.txt", true);
        fw.write("publishExtraOutputs called\n");
        fw.write("myWeights null? " + (todaysDailyResult.myWeights == null) + "\n");
        if (todaysDailyResult.myWeights != null) {
            fw.write("myWeights length: " + todaysDailyResult.myWeights.length + "\n");
            // Write the actual weights
            for (int i = 0; i < todaysDailyResult.myWeights.length; i++) {
                fw.write("Weight[" + i + "]: " + todaysDailyResult.myWeights[i] + "\n");
            }
        }
        fw.write("myThirdPartyIndexComps null? " + (myThirdPartyIndexComps == null) + "\n");
        if (myThirdPartyIndexComps != null) {
            fw.write("myThirdPartyIndexComps size: " + myThirdPartyIndexComps.size() + "\n");
            for (Map.Entry<String, Double> entry : myThirdPartyIndexComps.entrySet()) {
                fw.write(entry.getKey() + ": " + entry.getValue() + "\n");
            }
        }
        fw.write("---End of entry---\n");
        fw.close();
    } catch (Exception e) {
        // Silent fail
    }
    
    // Rest of your existing code...
    final String COST = "IndexFeeReport";
    // ... continue with existing publishExtraOutputs code ...
}


public void publishExtraOutputs(ExtraOutputCollector extraOutputsCollector, 
        PortfolioContextRepository portfolioRepository, 
        IndexSpecificDailyResult todaysDailyResult) throws AMGException {
    
    // Print weights to console
    System.out.println("========== WEIGHTS OUTPUT ==========");
    System.out.println("publishExtraOutputs called");
    
    if (todaysDailyResult.myWeights != null) {
        System.out.println("Weights array length: " + todaysDailyResult.myWeights.length);
        for (int i = 0; i < todaysDailyResult.myWeights.length; i++) {
            if (i < myIdentifier.size()) {
                System.out.println("Weight[" + myIdentifier.get(i).getMarketId() + "]: " + todaysDailyResult.myWeights[i]);
            } else {
                System.out.println("Weight[" + i + "]: " + todaysDailyResult.myWeights[i]);
            }
        }
    } else {
        System.out.println("myWeights is NULL");
    }
    
    if (myThirdPartyIndexComps != null) {
        System.out.println("ThirdPartyIndexComps:");
        for (Map.Entry<String, Double> entry : myThirdPartyIndexComps.entrySet()) {
            System.out.println("  " + entry.getKey() + ": " + entry.getValue());
        }
    }
    
    System.out.println("Index Price: " + todaysDailyResult.myPrice[0]);
    System.out.println("=====================================");
    
    // Your existing code continues...
    final String COST = "IndexFeeReport";
    // ... rest of existing code ...
}
