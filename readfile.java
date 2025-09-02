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



// Write weights to file for each date
try {
    // Define output file path - adjust as needed
    String outputPath = "C:/Users/xiazhu/Desktop/all_weights_history.csv";
    java.io.File file = new java.io.File(outputPath);
    boolean fileExists = file.exists() && file.length() > 0;
    
    // Open file in append mode
    java.io.PrintWriter writer = new java.io.PrintWriter(
        new java.io.FileWriter(outputPath, true)  // true = append mode
    );
    
    // Write header only if file is new
    if (!fileExists) {
        // Write header with Date and all underlier names
        writer.print("Date");
        for (Identifier id : myIdentifier) {
            writer.print("," + id.getMarketId());
        }
        writer.print(",CashWeight,Leverage,RiskyAssetSpot,IndexPrice");
        writer.println();
    }
    
    // Write data row for current date
    writer.print(valDate.toString());  // Current date
    
    // Write each weight
    for (double weight : todaysRebalanceResult.myWeights) {
        writer.print("," + String.format("%.6f", weight));
    }
    
    // Also write cash weight, leverage, and other useful info
    writer.print("," + String.format("%.6f", todaysRebalanceResult.myCashWeight));
    writer.print("," + String.format("%.6f", todaysRebalanceResult.myLeverage));
    writer.print("," + String.format("%.6f", todaysRebalanceResult.myRiskyAssetSpot));
    writer.print("," + String.format("%.6f", todaysRebalanceResult.myPrice[0]));
    
    writer.println();
    writer.close();
    
    // Optional: Also create a detailed text file for easier reading
    java.io.PrintWriter txtWriter = new java.io.PrintWriter(
        new java.io.FileWriter("C:/Users/xiazhu/Desktop/weights_detailed_history.txt", true)
    );
    
    txtWriter.println("=== Date: " + valDate.toString() + " ===");
    for (int i = 0; i < myIdentifier.size(); i++) {
        txtWriter.println("  " + myIdentifier.get(i).getMarketId() + ": " + 
                         String.format("%.6f", todaysRebalanceResult.myWeights[i]) + 
                         " (BBG: " + myIdentifier.get(i).getBbgId() + ")");
    }
    txtWriter.println("  Cash Weight: " + String.format("%.6f", todaysRebalanceResult.myCashWeight));
    txtWriter.println("  Total Leverage: " + String.format("%.6f", todaysRebalanceResult.myLeverage));
    txtWriter.println("  Index Price: " + String.format("%.6f", todaysRebalanceResult.myPrice[0]));
    txtWriter.println();
    txtWriter.close();
    
} catch (java.io.IOException e) {
    // Log error but don't fail the entire process
    System.err.println("Warning: Could not write weights to file: " + e.getMessage());
    // Optionally throw if you want to stop on file write errors:
    // throw new AMGException("Failed to write weights history: " + e.getMessage());
}



// Minimal test - write to current directory with simple name
try {
    // Create a very simple file in current directory
    java.io.FileWriter fw = new java.io.FileWriter("WEIGHTS_TEST.txt", true);
    fw.write("Date: " + valDate.toString() + "\n");
    fw.write("Weights count: " + todaysRebalanceResult.myWeights.length + "\n");
    for (int i = 0; i &lt; todaysRebalanceResult.myWeights.length; i++) {
        fw.write("Weight " + i + ": " + todaysRebalanceResult.myWeights[i] + "\n");
    }
    fw.write("---\n");
    fw.close();
    
    // Also try to create a marker file to prove code executed
    java.io.FileWriter marker = new java.io.FileWriter("MARKER_FILE_" + System.currentTimeMillis() + ".txt");
    marker.write("This file proves the code executed at: " + new java.util.Date());
    marker.close();
    
} catch (Exception e) {
    // Create an error file if something goes wrong
    try {
        java.io.FileWriter errorFile = new java.io.FileWriter("ERROR_LOG.txt", true);
        errorFile.write("Error at " + valDate + ": " + e.getMessage() + "\n");
        errorFile.close();
    } catch (Exception e2) {
        // If we can't even write an error file, there's a serious permission issue
    }
}


// Debug: Find out where files are actually being written
try {
    // Get absolute path information
    java.io.File currentDir = new java.io.File(".");
    String absolutePath = currentDir.getAbsolutePath();
    
    // Create a file with the absolute path in its name
    String fileName = "WEIGHTS_LOCATION_" + absolutePath.replace(":", "").replace("\\", "_").replace("/", "_") + ".txt";
    java.io.FileWriter fw = new java.io.FileWriter(fileName);
    fw.write("Current working directory: " + absolutePath + "\n");
    fw.write("User home: " + System.getProperty("user.home") + "\n");
    fw.write("User dir: " + System.getProperty("user.dir") + "\n");
    fw.write("Temp dir: " + System.getProperty("java.io.tmpdir") + "\n");
    fw.write("Date: " + valDate.toString() + "\n");
    fw.close();
    
    // Also write to absolute path on Desktop
    String desktopPath = "C:\\Users\\xiazhu\\Desktop\\WEIGHTS_ABSOLUTE_TEST.txt";
    java.io.FileWriter desktopWriter = new java.io.FileWriter(desktopPath, true);
    desktopWriter.write("Successfully wrote at: " + new java.util.Date() + "\n");
    desktopWriter.write("Date: " + valDate.toString() + "\n");
    desktopWriter.close();
    
} catch (Exception e) {
    // Try writing error to desktop
    try {
        String errorPath = "C:\\Users\\xiazhu\\Desktop\\WRITE_ERROR.txt";
        java.io.FileWriter errorWriter = new java.io.FileWriter(errorPath);
        errorWriter.write("Error: " + e.getMessage() + "\n");
        errorWriter.write("Stack trace:\n");
        for (StackTraceElement elem : e.getStackTrace()) {
            errorWriter.write(elem.toString() + "\n");
        }
        errorWriter.close();
    } catch (Exception e2) {
        // Silent fail
    }
}



// Debug: Find out where files are actually being written
try {
    // Get absolute path information
    java.io.File currentDir = new java.io.File(".");
    String absolutePath = currentDir.getAbsolutePath();
    
    // Create a file with the absolute path in its name
    String fileName = "WEIGHTS_LOCATION_" + absolutePath.replace(":", "").replace("\\", "_").replace("/", "_") + ".txt";
    java.io.FileWriter fw = new java.io.FileWriter(fileName);
    fw.write("Current working directory: " + absolutePath + "\n");
    fw.write("User home: " + System.getProperty("user.home") + "\n");
    fw.write("User dir: " + System.getProperty("user.dir") + "\n");
    fw.write("Temp dir: " + System.getProperty("java.io.tmpdir") + "\n");
    fw.write("Date: " + valDate.toString() + "\n");
    fw.close();
    
    // Also write to absolute path on Desktop
    String desktopPath = "C:\\Users\\xiazhu\\Desktop\\WEIGHTS_ABSOLUTE_TEST.txt";
    java.io.FileWriter desktopWriter = new java.io.FileWriter(desktopPath, true);
    desktopWriter.write("Successfully wrote at: " + new java.util.Date() + "\n");
    desktopWriter.write("Date: " + valDate.toString() + "\n");
    desktopWriter.close();
    
} catch (Exception e) {
    // Try writing error to desktop
    try {
        String errorPath = "C:\\Users\\xiazhu\\Desktop\\WRITE_ERROR.txt";
        java.io.FileWriter errorWriter = new java.io.FileWriter(errorPath);
        errorWriter.write("Error: " + e.getMessage() + "\n");
        errorWriter.write("Stack trace:\n");
        for (StackTraceElement elem : e.getStackTrace()) {
            errorWriter.write(elem.toString() + "\n");
        }
        errorWriter.close();
    } catch (Exception e2) {
        // Silent fail
    }
}


// Write to system output instead of file
System.out.println("===== WEIGHTS OUTPUT =====");
System.out.println("Date: " + valDate.toString());
System.out.println("Weights array length: " + todaysRebalanceResult.myWeights.length);
for (int i = 0; i < todaysRebalanceResult.myWeights.length; i++) {
    System.out.println("Weight[" + i + "] = " + todaysRebalanceResult.myWeights[i]);
}
System.out.println("==========================");






public void publishExtraOutputs(ExtraOutputCollector extraOutputsCollector, 
        PortfolioContextRepository portfolioRepository, 
        IndexSpecificDailyResult todaysDailyResult) throws AMGException {
    
    try {
        // Get the current date from the portfolio context
        LibAMGDate currentDate = portfolioRepository.getPortfolioProvider().getMainPortfolio().getDate();
        
        // Write weights to file
        java.io.FileWriter fw = new java.io.FileWriter("C:\\Users\\xiazhu\\Desktop\\ALL_WEIGHTS_HISTORY.csv", true);
        
        // Check if file is new to write header
        java.io.File file = new java.io.File("C:\\Users\\xiazhu\\Desktop\\ALL_WEIGHTS_HISTORY.csv");
        if (file.length() == 0) {
            // Write header
            fw.write("Date");
            for (Identifier id : myIdentifier) {
                fw.write("," + id.getMarketId());
            }
            fw.write("\n");
        }
        
        // Write date
        fw.write(currentDate.toString());
        
        // Write weights - check if myWeights is populated
        if (todaysDailyResult.myWeights != null && todaysDailyResult.myWeights.length > 0) {
            // Use the calculated weights
            for (double weight : todaysDailyResult.myWeights) {
                fw.write("," + weight);
            }
        } else {
            // Fall back to myThirdPartyIndexComps if myWeights isn't populated
            for (Identifier id : myIdentifier) {
                Double weight = myThirdPartyIndexComps.get(id.getMarketId());
                fw.write("," + (weight != null ? weight : "0.0"));
            }
        }
        fw.write("\n");
        fw.close();
        
    } catch (Exception e) {
        // Try to write error log
        try {
            java.io.FileWriter errorLog = new java.io.FileWriter("C:\\Users\\xiazhu\\Desktop\\WEIGHTS_ERROR.txt", true);
            errorLog.write("Error at publishExtraOutputs: " + e.getMessage() + "\n");
            errorLog.close();
        } catch (Exception e2) {
            // Silent fail
        }
    }
    
    // Existing code...
    extraOutputsCollector.value(Publish, ExtraOutputs.key(INDEX_FEE_REPORT, INDEX_PRICE), todaysDailyResult.myPrice);
    // ... rest of existing code ...
}
