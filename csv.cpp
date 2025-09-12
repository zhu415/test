std::ofstream csvFile("softcall_probabilities.csv");
                if (csvFile.is_open())
                {
                    // Write header
                    csvFile << "Index,Spot,Volatility,Probability\n";
                    
                    // Write data
                    for (size_t i = 0; i < spots.size(); ++i)
                    {
                        csvFile << i << "," 
                                << spots[i] << "," 
                                << vols[i] << "," 
                                << prob[i] << "\n";
                    }
                    
                    csvFile.close();
                }
