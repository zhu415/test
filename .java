@Override
public double getRealizedVarianceEstimate() {
    double[][] returns = getReturnHistoryVectors();
    int assetNum = myAssets.length;
    
    try {
        // Use the helper method without funding cost adjustment
        WeightCalculationResult calcResult = parent.calculateWeightsAndVolatility(
            returns, null, null, false);
        
        // Calculate sum_i(VolatilityContribution_i / vol63_i)
        double sumVolContribOverVol = 0.0;
        for (int i = 0; i < assetNum; i++) {
            double vol63 = Math.sqrt(calcResult.covar63[i][i] * 252);
            sumVolContribOverVol += calcResult.volatilityContribution[i] / Math.max(vol63, 0.0001);
        }
        
        // Calculate realized variance estimate
        double maxPortfolioVol = Math.max(calcResult.portfolioVolatility21, calcResult.portfolioVolatility63);
        double realizedVolEstimate = (maxPortfolioVol / parent.myVolatilityTarget) / sumVolContribOverVol;
        
        return realizedVolEstimate * realizedVolEstimate;
    } catch (AMGException e) {
        throw new RuntimeException("Error calculating realized variance estimate", e);
    }
}


// Add this helper class to encapsulate the calculation results
private static class WeightCalculationResult {
    double[] volatilityContribution;
    double[] initialWeight;
    double sumInitialWeights;
    double[][] covar21;
    double[][] covar63;
    double portfolioVolatility21;
    double portfolioVolatility63;
    double scalingFactor;
}

// Add this helper method
private WeightCalculationResult calculateWeightsAndVolatility(
        double[][] returns, 
        DynamicIndexEvolutionContext context,
        LibAMGDate refDate,
        boolean includeFundingCost) throws AMGException {
    
    int assetNum = myIndexComponents.length;
    WeightCalculationResult result = new WeightCalculationResult();
    
    result.covar21 = covariance(20, returns);
    result.covar63 = covariance(62, returns);
    
    result.volatilityContribution = new double[assetNum];
    
    if (isMomentumIndex()) {
        int rankedAssets = rankedAssets();
        Integer[] rank = new Integer[rankedAssets];
        final double[] perf = new double[assetNum];
        int iRanked = 0;
        
        for (int i = 0; i < assetNum; i++) {
            if (myIndexComponents[i].isRanked()) {
                double p = 0.0;
                LibAMGDate dt = refDate;
                for (double dar : returns[i]) {
                    p += dar;
                    if (includeFundingCost && context != null) {
                        LibAMGDate prevDt = myCalendars.addBusinessDays(dt, -1);
                        double dcf360 = (dt.getModifiedJulian() - prevDt.getModifiedJulian()) / 360.0;
                        p -= myIndexComponents[i].getFundingRate(prevDt, context) * dcf360;
                        dt = prevDt;
                    }
                }
                rank[iRanked] = Integer.valueOf(i);
                perf[i] = p;
                iRanked++;
            }
        }
        
        Comparator<Integer> comp = new Comparator<Integer>() {
            public int compare(Integer i1, Integer i2) {
                return perf[i1] > perf[i2] ? -1 : perf[i1] < perf[i2] ? +1 : i1 - i2;
            }
        };
        Arrays.sort(rank, comp);
        
        for (int i = 0; i < assetNum; i++) {
            if (!myIndexComponents[i].isRanked()) {
                result.volatilityContribution[i] = myIndexComponents[i].myVolatilityContribution;
            }
        }
        for (int i = 0; i < rankedAssets; i++) {
            result.volatilityContribution[rank[i]] = myVolatilityContributionPerRank[i];
        }
    } else {
        for (int i = 0; i < assetNum; i++) {
            result.volatilityContribution[i] = myIndexComponents[i].myVolatilityContribution;
        }
    }
    
    // Calculate initial weights
    result.initialWeight = new double[assetNum];
    result.sumInitialWeights = 0.0;
    double[] vol63 = new double[assetNum];
    
    for (int i = 0; i < assetNum; i++) {
        vol63[i] = Math.sqrt(result.covar63[i][i] * 252);
        result.initialWeight[i] = myVolatilityTarget * result.volatilityContribution[i] / Math.max(vol63[i], 0.0001);
        result.sumInitialWeights += result.initialWeight[i];
    }
    
    // Calculate portfolio volatilities
    result.portfolioVolatility21 = portfolioVolatility(result.initialWeight, result.covar21);
    result.portfolioVolatility63 = portfolioVolatility(result.initialWeight, result.covar63);
    
    // Calculate scaling factor
    result.scalingFactor = myVolatilityTarget / Math.max(result.portfolioVolatility21, result.portfolioVolatility63);
    
    return result;
}
