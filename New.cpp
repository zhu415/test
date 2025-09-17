template<class T1, class T2>
void validateCallSchedulesInConversionSchedules(
    const std::vector<T1>& conversionSchedule,
    const std::vector<T2>& callSchedule,
    const AMG::Dates::DateTime& buildDate)  // New parameter
{
    // Collect and sort conversion intervals, filtering out periods before build date
    std::vector<std::pair<AMG::Dates::DateTime, AMG::Dates::DateTime>> conversionIntervals;
    for (size_t i = 0; i < conversionSchedule.size(); ++i) {
        auto startDate = conversionSchedule[i].startDate();
        auto endDate = conversionSchedule[i].endDate();
        
        // Skip intervals that end before build date
        if (endDate < buildDate) {
            continue;
        }
        
        // Adjust start date if it's before build date
        if (startDate < buildDate) {
            startDate = buildDate;
        }
        
        conversionIntervals.emplace_back(startDate, endDate);
    }
    
    std::sort(conversionIntervals.begin(), conversionIntervals.end());
    
    // Check each call schedule (only those after build date)
    for (size_t i = 0; i < callSchedule.size(); ++i) {
        auto callStart = callSchedule[i].startDate();
        auto callEnd = callSchedule[i].endDate();
        
        // Skip validation for call schedules that end before build date
        if (callEnd < buildDate) {
            continue;
        }
        
        // Adjust call start date if it's before build date
        if (callStart < buildDate) {
            callStart = buildDate;
        }
        
        bool isSubset = false;
        
        // Check if this call schedule is fully contained in any conversion interval
        for (const auto& [convStart, convEnd] : conversionIntervals) {
            if (convStart <= callStart && callEnd <= convEnd) {
                isSubset = true;
                break;
            }
        }
        
        // Check consecutive adjacent intervals if needed
        if (!isSubset) {
            for (size_t j = 0; j < conversionIntervals.size(); ++j) {
                if (conversionIntervals[j].first <= callStart && 
                    callStart <= conversionIntervals[j].second) {
                    auto currentEnd = conversionIntervals[j].second;
                    if (callEnd <= currentEnd) {
                        isSubset = true;
                        break;
                    }
                    
                    // Check consecutive adjacent intervals
                    for (size_t k = j + 1; k < conversionIntervals.size(); ++k) {
                        if (conversionIntervals[k].first != currentEnd) {
                            break;  // Gap found
                        }
                        currentEnd = conversionIntervals[k].second;
                        if (callEnd <= currentEnd) {
                            isSubset = true;
                            break;
                        }
                    }
                    break;
                }
            }
        }
        
        if (!isSubset) {
            AMG_THROW("Call schedule [" + callStart.toString() + ", " + callEnd.toString() + 
                      "] at index " + std::to_string(i) + 
                      " is not a subset of the union of conversion schedules (validated from build date " +
                      buildDate.toString() + ")");
        }
    }
}
