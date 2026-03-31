package com.university.analytics.repository;

import com.university.analytics.model.AnalyticsRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface AnalyticsRepository extends JpaRepository<AnalyticsRecord, Long> {
    Optional<AnalyticsRecord> findByDigitalSignature(String signature);
}
