package com.example.batchprocessing.dto;

public record JobLaunchResponse(
        String jobId,
        String status,
        int recordsProcessed,
        String message
) {
    public static JobLaunchResponse success(String jobId, int records) {
        return new JobLaunchResponse(jobId, "COMPLETED", records, "Job executed successfully");
    }

    public static JobLaunchResponse error(String jobId, String errorMsg) {
        return new JobLaunchResponse(jobId, "FAILED", 0, errorMsg);
    }
}