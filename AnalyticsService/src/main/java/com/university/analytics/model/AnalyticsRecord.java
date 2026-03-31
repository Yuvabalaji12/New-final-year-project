package com.university.analytics.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "analytics_records")
public class AnalyticsRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "student_id", length = 100)
    private String studentId;

    @Column(name = "course_name", length = 200)
    private String courseName;

    @Column(name = "digital_signature", length = 2048)
    private String digitalSignature;

    @Column(name = "issued_at")
    private LocalDateTime issuedAt;

    public AnalyticsRecord() {
    }

    public AnalyticsRecord(String studentId, String courseName, String digitalSignature, LocalDateTime issuedAt) {
        this.studentId = studentId;
        this.courseName = courseName;
        this.digitalSignature = digitalSignature;
        this.issuedAt = issuedAt;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getStudentId() { return studentId; }
    public void setStudentId(String studentId) { this.studentId = studentId; }
    public String getCourseName() { return courseName; }
    public void setCourseName(String courseName) { this.courseName = courseName; }
    public String getDigitalSignature() { return digitalSignature; }
    public void setDigitalSignature(String digitalSignature) { this.digitalSignature = digitalSignature; }
    public LocalDateTime getIssuedAt() { return issuedAt; }
    public void setIssuedAt(LocalDateTime issuedAt) { this.issuedAt = issuedAt; }
}
