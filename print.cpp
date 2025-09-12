// Helper function to print table header
            void printTableHeader(std::ostream& out, bool includeVolatility = true)
            {
                out << std::setw(10) << "Index" 
                    << std::setw(15) << "Spot" 
                    << std::setw(15) << "Probability";
                if (includeVolatility) {
                    out << std::setw(15) << "Volatility";
                }
                out << std::setw(20) << "Above Barrier?" << std::endl;
                
                out << std::string(60 + (includeVolatility ? 15 : 0), '-') << std::endl;
            }
            
            // Helper function to print a single row
            void printTableRow(std::ostream& out, size_t index, double spot, double probability, 
                              double volatility, double barrier, bool includeVolatility = true)
            {
                out << std::setw(10) << index
                    << std::setw(15) << std::fixed << std::setprecision(6) << spot
                    << std::setw(15) << std::fixed << std::setprecision(8) << probability;
                if (includeVolatility) {
                    out << std::setw(15) << std::fixed << std::setprecision(6) << volatility;
                }
                out << std::setw(20) << (spot > barrier ? "Yes" : "No") << std::endl;
            }


// Print table to console if requested
                if (printTable) {
                    std::cout << "\n=== Soft Call Probability Table ===" << std::endl;
                    std::cout << "Barrier: " << barrier << std::endl;
                    std::cout << "Quantile: " << quantile << std::endl;
                    std::cout << "Time: " << time << std::endl;
                    std::cout << "Drift: " << drift << std::endl;
                    std::cout << std::endl;
                    
                    printTableHeader(std::cout);
                    for (size_t i = 0; i < spots.size(); ++i) {
                        printTableRow(std::cout, i, spots[i], prob[i], vols[i], barrier);
                    }
                    
                    // Print summary statistics
                    double avgProb = 0.0;
                    double maxProb = prob[0];
                    double minProb = prob[0];
                    size_t aboveBarrierCount = 0;
                    
                    for (size_t i = 0; i < prob.size(); ++i) {
                        avgProb += prob[i];
                        maxProb = std::max(maxProb, prob[i]);
                        minProb = std::min(minProb, prob[i]);
                        if (spots[i] > barrier) aboveBarrierCount++;
                    }
                    avgProb /= prob.size();
                    
                    std::cout << "\n--- Summary Statistics ---" << std::endl;
                    std::cout << "Total points: " << spots.size() << std::endl;
                    std::cout << "Points above barrier: " << aboveBarrierCount << std::endl;
                    std::cout << "Average probability: " << std::fixed << std::setprecision(8) << avgProb << std::endl;
                    std::cout << "Min probability: " << minProb << std::endl;
                    std::cout << "Max probability: " << maxProb << std::endl;
                }
                
                // Write to file if filename provided
                if (!outputFile.empty()) {
                    std::ofstream file(outputFile);
                    if (file.is_open()) {
                        file << "Soft Call Probability Results" << std::endl;
                        file << "=============================" << std::endl;
                        file << "Barrier," << barrier << std::endl;
                        file << "Quantile," << quantile << std::endl;
                        file << "Time," << time << std::endl;
                        file << "Drift," << drift << std::endl;
                        file << std::endl;
                        file << "Index,Spot,Probability,Volatility,Above_Barrier" << std::endl;
                        
                        for (size_t i = 0; i < spots.size(); ++i) {
                            file << i << "," 
                                 << spots[i] << "," 
                                 << prob[i] << "," 
                                 << vols[i] << ","
                                 << (spots[i] > barrier ? "Yes" : "No") << std::endl;
                        }
                        file.close();
                        std::cout << "Results written to: " << outputFile << std::endl;
                    } else {
                        std::cerr << "Unable to open file: " << outputFile << std::endl;
                    }
                }
            }
