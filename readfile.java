Approach 1: Add File Writing in the publishExtraOutputs Method
public void publishExtraOutputs(ExtraOutputCollector extraOutputsCollector, PortfolioContextRepository portfolioRepository, IndexSpecificDailyResult todaysDailyResult) throws AMGException {
    // ... existing code ...
    
    // Add file writing for weights
    try {
        // Create a timestamp for unique filenames
        String timestamp = new java.text.SimpleDateFormat("yyyyMMdd_HHmmss").format(new java.util.Date());
        String fileName = "weights_output_" + timestamp + ".csv";
        
        java.io.PrintWriter writer = new java.io.PrintWriter(new java.io.FileWriter(fileName, true));
        
        // Write header if file is new
        writer.println("Date,Underlier,Weight");
        
        // Write weights data
        for (int i = 0; i < myIdentifier.size(); i++) {
            writer.println(todayManager.getValDate() + "," + 
                          myIdentifier.get(i).getMarketId() + "," + 
                          todaysDailyResult.myWeights[i]);
        }
        
        writer.close();
        
        // Also write to a simple text file for easy viewing
        java.io.PrintWriter txtWriter = new java.io.PrintWriter(new java.io.FileWriter("weights_latest.txt"));
        txtWriter.println("Latest Weights - Date: " + todayManager.getValDate());
        txtWriter.println("=====================================");
        for (int i = 0; i < myIdentifier.size(); i++) {
            txtWriter.println(myIdentifier.get(i).getMarketId() + ": " + todaysDailyResult.myWeights[i]);
        }
        txtWriter.println("Total Weight: " + java.util.Arrays.stream(todaysDailyResult.myWeights).sum());
        txtWriter.close();
        
    } catch (java.io.IOException e) {
        throw new AMGException("Failed to write weights to file: " + e.getMessage());
    }
    
    // ... rest of existing code ...
}





Approach 2: Add File Writing in the rebalance Method
// After this line:
todaysRebalanceResult.myWeights = myIdentifier.stream().mapToDouble(x -> myThirdPartyIndexComps.get(x.getMarketId())).toArray();

// Add file writing:
try {
    // Write to CSV
    java.io.PrintWriter csvWriter = new java.io.PrintWriter(
        new java.io.FileWriter("C:/Users/xiazhu/Desktop/weights_output.csv", true)
    );
    
    // Write header only once (check if file exists first)
    java.io.File file = new java.io.File("C:/Users/xiazhu/Desktop/weights_output.csv");
    if (file.length() == 0) {
        csvWriter.print("Date");
        for (Identifier id : myIdentifier) {
            csvWriter.print("," + id.getMarketId());
        }
        csvWriter.println();
    }
    
    // Write data row
    csvWriter.print(valDate.toString());
    for (double weight : todaysRebalanceResult.myWeights) {
        csvWriter.print("," + weight);
    }
    csvWriter.println();
    csvWriter.close();
    
} catch (java.io.IOException e) {
    // Log error but don't fail the process
    System.err.println("Warning: Could not write weights to file: " + e.getMessage());
}
