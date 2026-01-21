// =============================================================================
// FIX: CurrencyOverride with ForwardCalculator Currency Inversion
// =============================================================================
//
// Problem: 
//   Currency=USD, DisplayCurrency=BRL
//   ForwardCalculator: myBumpedValue /= mySpot (bumped spot)
//   CurrencyOverride:  fx * myUnbumpedDisplayFX * valueInProductCurrency
//
//   For Delta calculation:
//     V_up   = (PV_up / S_up) * unbumpedDisplayFX  
//     V_down = (PV_down / S_down) * unbumpedDisplayFX
//
//   The S_up and S_down are different, but unbumpedDisplayFX is constant.
//   This is inconsistent - either both should use bumped FX or both unbumped.
//
// Solution:
//   Pass unbumped spot to ForwardCalculator for the inversion, so:
//     V_up   = (PV_up / S_unbumped) * unbumpedDisplayFX  
//     V_down = (PV_down / S_unbumped) * unbumpedDisplayFX
//
//   This makes the conversion consistent.
// =============================================================================

// -----------------------------------------------------------------------------
// FILE 1: Add to EvaluationArgs class (in RiskEvaluator.hpp or similar)
// -----------------------------------------------------------------------------

// Add these members and methods to EvaluationArgs:

/*
private:
    double myUnbumpedSpotForInversion = Consts::NaN();

public:
    void setUnbumpedSpotForInversion(double spot) 
    { 
        myUnbumpedSpotForInversion = spot; 
    }
    
    double getUnbumpedSpotForInversion() const 
    { 
        return myUnbumpedSpotForInversion; 
    }
    
    bool hasUnbumpedSpotForInversion() const 
    { 
        return !Utils::isNaN(myUnbumpedSpotForInversion); 
    }
*/


// -----------------------------------------------------------------------------
// FILE 2: CurrencyOverride.cpp - Modify CurrencyOverrideEvaluator
// -----------------------------------------------------------------------------

class CurrencyOverrideEvaluator : public RecursiveEvaluator
{
public:
    CurrencyOverrideEvaluator(
        IEvaluate& evaluator,
        const double centralValueInProductCurrency,
        const double centralValueInGivenCurrency,
        const double unbumpedDisplayFX,
        const std::shared_ptr<const Indices::Currency>& currency,
        const std::shared_ptr<const Indices::Currency>& displayCurrency,
        const double unbumpedSpotForInversion)  // <-- ADD THIS PARAMETER
        : Risk::RecursiveEvaluator(evaluator, centralValueInGivenCurrency)
        , myCurrency(currency)
        , myDisplayCurrency(displayCurrency)
        , myCentralValueInProductCurrency(centralValueInProductCurrency)
        , myUnbumpedDisplayFX(unbumpedDisplayFX)
        , myUnbumpedSpotForInversion(unbumpedSpotForInversion)  // <-- ADD THIS
        , myIndependentRisk(false)
    {
    }
    
    double evaluateBumped(
        const Models::ModelBase& model, 
        const Dates::DateTime& valDate, 
        const EvaluationArgs* args = nullptr) override
    {
        const std::shared_ptr<const Indices::Currency>& foreign = 
            RecursiveEvaluator::getCurrency();
        const double fx = Models::FXForwardBase::getSpotFX(
            model.shared_from_this(), myCurrency, foreign, valDate);

        double valueInProductCurrency = Consts::NaN();
        
        // --- ADD THIS BLOCK ---
        // Create modified args with unbumped spot for ForwardCalculator
        EvaluationArgs modifiedArgs;
        if (args)
            modifiedArgs = *args;
        
        // Pass unbumped spot so ForwardCalculator uses consistent FX for inversion
        if (!Utils::isNaN(myUnbumpedSpotForInversion))
            modifiedArgs.setUnbumpedSpotForInversion(myUnbumpedSpotForInversion);
        // --- END ADD ---
        
        if (myIndependentRisk)
            valueInProductCurrency = myCentralValueInProductCurrency;
        else
            valueInProductCurrency = RecursiveEvaluator::evaluateBumped(
                model, valDate, &modifiedArgs);  // <-- Pass modifiedArgs
        
        return fx * myUnbumpedDisplayFX * valueInProductCurrency;
    }
    
    std::shared_ptr<const Indices::Currency> getCurrency() const override
    {
        return myDisplayCurrency;
    }
    
    std::shared_ptr<const Indices::Currency> getCurrencyOrOverride() const override
    {
        return myCurrency;
    }
    
    void setIndependentRisk(bool f) { myIndependentRisk = f; }
    
private:
    std::shared_ptr<const Indices::Currency> myCurrency;
    std::shared_ptr<const Indices::Currency> myDisplayCurrency;
    double myCentralValueInProductCurrency;
    double myUnbumpedDisplayFX;
    double myUnbumpedSpotForInversion;  // <-- ADD THIS MEMBER
    bool myIndependentRisk;
};


// -----------------------------------------------------------------------------
// FILE 2: CurrencyOverride.cpp - Modify CurrencyOverrideResult::describeRisk
// -----------------------------------------------------------------------------

void describeRisk(
    IEvaluate& evaluator,
    const std::shared_ptr<const Models::ModelBase>& unbumpedModel,
    Description::Document& results,
    RiskValues& values,
    const std::shared_ptr<const Fixings::IFixings>& fixingsOrNull = nullptr,
    bool /*wantScaledOutput*/ = false) const override
{
    AMGTIMER(dR, "CurrencyOverride", "CurrencyOverrideResult_describeRisk")

    results.start(CurrencyOverride::ourClassTag);
    results.describe(&myId, Writer::RISK_ID_TAG, 
                     "Name of the associated risk request");
    
    const double fx = Models::FXForwardBase::getSpotFX(
        unbumpedModel, myCurrency, evaluator.getCurrency(), myValDate);
    const double displayFX = Models::FXForwardBase::getSpotFX(
        unbumpedModel, myDisplayCurrency, myCurrency, myValDate);
    const double unbumpedValue = evaluator.evaluateUnbumped();
    
    // --- ADD THIS BLOCK ---
    // Get unbumped spot for FX inversion in ForwardCalculator
    // This ensures consistency: if we use unbumpedDisplayFX, we should also
    // use unbumped spot for the inversion in ForwardCalculator
    double unbumpedSpotForInversion = Consts::NaN();
    try
    {
        // For BRL/USD forward with Currency=USD:
        // evaluator.getCurrency() = product currency (BRL after ForwardCalculator inversion = USD? 
        //                           or original BRL?)
        // We need the BRL/USD spot from unbumped model
        
        // The spot needed depends on the FX pair in the forward contract
        // Typically: spot = foreign/domestic where domestic = myCurrency
        unbumpedSpotForInversion = Models::FXForwardBase::getSpotFX(
            unbumpedModel, 
            evaluator.getCurrency(),  // Original product currency (BRL)
            myCurrency,               // CurrencyOverride currency (USD)
            myValDate);
    }
    catch (const Utils::Exception&)
    {
        // If we can't get it, ForwardCalculator will use its own (bumped) spot
    }
    // --- END ADD ---
    
    CurrencyOverrideEvaluator subEvaluator(
        evaluator, 
        unbumpedValue, 
        fx * displayFX * unbumpedValue, 
        displayFX, 
        myCurrency, 
        myDisplayCurrency,
        unbumpedSpotForInversion);  // <-- ADD THIS ARGUMENT

    const size_t nRisks = myRiskResults.size();
    for (size_t i = 0; i < nRisks; ++i)
    {
        subEvaluator.setIndependentRisk(
            myOptimiseIndependentRisks && myRiskResults[i]->isAlwaysZero(evaluator));
        myRiskResults[i]->describeRisk(
            subEvaluator, unbumpedModel, results, values, fixingsOrNull);
    }
    results.end(CurrencyOverride::ourClassTag);
}


// -----------------------------------------------------------------------------
// FILE 3: ForwardCalculator.cpp - Modify evaluateBumped
// -----------------------------------------------------------------------------

// At the end of evaluateBumped, REPLACE:
/*
    if (myForwardContract && myForwardContract->getNeedsCurrencyInversion())
        myBumpedValue /= mySpot;
    return myBumpedValue;
*/

// WITH:

    if (myForwardContract && myForwardContract->getNeedsCurrencyInversion())
    {
        // When called from CurrencyOverride, use unbumped spot for consistency
        // with unbumpedDisplayFX. Otherwise use current (bumped) spot.
        double spotForInversion = mySpot;
        
        if (args && args->hasUnbumpedSpotForInversion())
        {
            spotForInversion = args->getUnbumpedSpotForInversion();
        }
        
        myBumpedValue /= spotForInversion;
    }
    return myBumpedValue;


// =============================================================================
// MATHEMATICAL JUSTIFICATION
// =============================================================================
//
// Let PV(S) = present value in BRL as function of spot S
// Let S_0 = unbumped spot (BRL/USD)
// Let S_up, S_down = bumped spots
//
// WITHOUT FIX (current behavior):
//   V_up   = PV(S_up) / S_up * displayFX_unbumped
//   V_down = PV(S_down) / S_down * displayFX_unbumped
//
//   Delta = (V_up - V_down) / (S_up - S_down)
//         = displayFX_unbumped * (PV(S_up)/S_up - PV(S_down)/S_down) / (S_up - S_down)
//
//   This mixes the derivative of PV with respect to S AND the derivative of 1/S
//
// WITH FIX:
//   V_up   = PV(S_up) / S_0 * displayFX_unbumped
//   V_down = PV(S_down) / S_0 * displayFX_unbumped
//
//   Delta = (V_up - V_down) / (S_up - S_down)
//         = (displayFX_unbumped / S_0) * (PV(S_up) - PV(S_down)) / (S_up - S_down)
//         = (displayFX_unbumped / S_0) * dPV/dS
//
//   This correctly scales the PV delta by a constant conversion factor.
//
// =============================================================================
