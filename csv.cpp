template<class T>
void validateCallSchedulesInConversionSchedules(
    const std::vector<T>& conversionSchedule,
    const std::vector<T>& callSchedule)
{
    // Since intervals don't overlap, we can simply sort them by start date
    // and check if each call schedule falls within the covered ranges
    
    // Collect and sort conversion intervals (no merging needed since no overlaps)
    std::vector<std::pair<AMG::Dates::DateTime, AMG::Dates::DateTime>> conversionIntervals;
    for (size_t i = 0; i < conversionSchedule.size(); ++i) {
        conversionIntervals.emplace_back(
            conversionSchedule[i].startDate(),
            conversionSchedule[i].endDate()
        );
    }
    
    // Sort by start date (assuming they don't overlap, this gives us ordered intervals)
    std::sort(conversionIntervals.begin(), conversionIntervals.end());
    
    // Check each call schedule
    for (size_t i = 0; i < callSchedule.size(); ++i) {
        auto callStart = callSchedule[i].startDate();
        auto callEnd = callSchedule[i].endDate();
        
        bool isSubset = false;
        
        // Since conversion intervals don't overlap but might be adjacent,
        // we need to check if the call schedule is covered by consecutive intervals
        size_t startIdx = 0;
        
        // Find which interval contains or could start containing the call schedule
        for (size_t j = 0; j < conversionIntervals.size(); ++j) {
            if (conversionIntervals[j].first <= callStart && 
                callStart <= conversionIntervals[j].second) {
                startIdx = j;
                
                // Check if it's fully contained in this single interval
                if (callEnd <= conversionIntervals[j].second) {
                    isSubset = true;
                    break;
                }
                
                // Otherwise, check if consecutive intervals cover it
                auto currentEnd = conversionIntervals[j].second;
                for (size_t k = j + 1; k < conversionIntervals.size(); ++k) {
                    // Check if next interval is adjacent (no gap)
                    if (conversionIntervals[k].first != currentEnd) {
                        break; // Gap found, can't be subset
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
        
        if (!isSubset) {
            AMG_THROW("Call schedule [" + callStart.toString() + ", " + callEnd.toString() + 
                      "] at index " + std::to_string(i) + 
                      " is not a subset of the union of conversion schedules");
        }
    }
}
