template<class T1, class T2>
void validateCallSchedulesInConversionSchedules(
    const std::vector<T1>& conversionSchedule,
    const std::vector<T2>& callSchedule,
    const AMG::Dates::DateTime& buildDate)
{
    // Collect only relevant conversion intervals
    std::vector<std::pair<AMG::Dates::DateTime, AMG::Dates::DateTime>> conversionIntervals;
    for (size_t i = 0; i < conversionSchedule.size(); ++i) {
        const auto& startDate = conversionSchedule[i].startDate();
        const auto& endDate = conversionSchedule[i].endDate();
        
        // Only include intervals that are active after build date
        if (endDate >= buildDate) {
            // Truncate the interval at build date if it starts before
            conversionIntervals.emplace_back(
                std::max(startDate, buildDate),
                endDate
            );
        }
    }
    
    if (conversionIntervals.empty()) {
        // No conversion schedules after build date, so nothing to validate against
        return;  // or throw an error if this shouldn't happen
    }
    
    std::sort(conversionIntervals.begin(), conversionIntervals.end());
    
    // Validate only call schedules that are active after build date
    for (size_t i = 0; i < callSchedule.size(); ++i) {
        const auto& originalCallStart = callSchedule[i].startDate();
        const auto& originalCallEnd = callSchedule[i].endDate();
        
        // Skip call schedules entirely before build date
        if (originalCallEnd < buildDate) {
            continue;
        }
        
        // For partially overlapping call schedules, validate only the part after build date
        auto callStart = std::max(originalCallStart, buildDate);
        auto callEnd = originalCallEnd;
        
        // ... rest of validation logic remains the same ...
        bool isSubset = false;
        // [validation code as before]
        
        if (!isSubset) {
            AMG_THROW("Call schedule [" + callStart.toString() + ", " + callEnd.toString() + 
                      "] at index " + std::to_string(i) + 
                      " (effective from build date) is not a subset of the union of conversion schedules");
        }
    }
}
