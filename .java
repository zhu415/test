@Override
public double getRealizedVarianceEstimate() {
    MultiAsset index = (MultiAsset) getIndex();
    int assetNum = myAssets.length;
    
    // Get fresh return history
    double[][] returns = getReturnHistoryVectors();
    
    // Check if we have enough history
    if (getReturnHistotyLength() < 63) {
        return Double.NaN;
    }
    
    // Calculate covariance matrices with current data
    double[][] covar21 = index.covariance(20, returns);
    double[][] covar63 = index.covariance(62, returns);
    
    // Get volatility contributions (same logic as in setEffectiveWeightsAndLastRebalanceDay)
    double[] volatilityContribution = new double[assetNum];
    
    if (index.isMomentumIndex()) {
        int rankedAssets = index.rankedAssets();
        Integer[] rank = new Integer[rankedAssets];
        final double[] perf = new double[assetNum];
        int iRanked = 0;
        
        for (int i = 0; i < assetNum; i++) {
            if (index.myIndexComponents[i].isRanked()) {
                double p = 0.0;
                LibAMGDate dt = getDate();
                for (double dar : returns[i]) {
                    p += dar;
                    LibAMGDate prevDt = index.myCalendars.addBusinessDays(dt, -1);
                    double dcf360 = (dt.getModifiedJulian() - prevDt.getModifiedJulian()) / 360.0;
                    p -= index.myIndexComponents[i].getFundingRate(prevDt, null) * dcf360;
                    dt = prevDt;
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
            if (!index.myIndexComponents[i].isRanked()) {
                volatilityContribution[i] = index.myIndexComponents[i].myVolatilityContribution;
            }
        }
        for (int i = 0; i < rankedAssets; i++) {
            volatilityContribution[rank[i]] = index.myVolatilityContributionPerRank[i];
        }
    } else {
        for (int i = 0; i < assetNum; i++) {
            volatilityContribution[i] = index.myIndexComponents[i].myVolatilityContribution;
        }
    }
    
    // Calculate initial weights and sum
    double[] initialWeight = new double[assetNum];
    double sumInitialWeights = 0.0;
    for (int i = 0; i < assetNum; i++) {
        double vol63 = Math.sqrt(covar63[i][i] * 252);
        initialWeight[i] = index.myVolatilityTarget * volatilityContribution[i] / Math.max(vol63, 0.0001);
        sumInitialWeights += initialWeight[i];
    }
    
    // Calculate portfolio volatilities
    double portfolioVolatility21 = index.portfolioVolatility(initialWeight, covar21);
    double portfolioVolatility63 = index.portfolioVolatility(initialWeight, covar63);
    
    // Calculate realized variance estimate using your formula:
    // (max(PortfolioVolatility21, PortfolioVolatility63) / myVolatilityTarget) / sum_i(VolatilityContribution_i / Vol63_i)
    double maxPortfolioVol = Math.max(portfolioVolatility21, portfolioVolatility63);
    double sumVolContributionOverVol63 = sumInitialWeights / index.myVolatilityTarget;
    
    return (maxPortfolioVol / index.myVolatilityTarget) / sumVolContributionOverVol63;
}
