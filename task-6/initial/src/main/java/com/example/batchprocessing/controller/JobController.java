package com.example.batchprocessing.controller;

import com.example.batchprocessing.dto.JobLaunchResponse;
import org.springframework.batch.core.*;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.batch.core.repository.JobExecutionAlreadyRunningException;
import org.springframework.batch.core.repository.JobInstanceAlreadyCompleteException;
import org.springframework.batch.core.repository.JobRestartException;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;

@RestController
@RequestMapping("/api/v1/jobs")
public class JobController {

    private final JobLauncher jobLauncher;
    private final Job importProductJob;  // имя бина из BatchConfiguration

    // Конструкторная инъекция (рекомендуется в Spring Boot 3)
    public JobController(
            JobLauncher jobLauncher,
            @Qualifier("importProductJob") Job importProductJob) {
        this.jobLauncher = jobLauncher;
        this.importProductJob = importProductJob;
    }

    @PostMapping("/import")
    public ResponseEntity<JobLaunchResponse> launchImportJob() {
        try {
            // ✅ FIX 1: Используем addLong вместо addInstant
            JobParameters jobParameters = new JobParametersBuilder()
                    .addLong("run.at", System.currentTimeMillis())
                    .addString("triggered.by", "api")
                    .toJobParameters();

            JobExecution execution = jobLauncher.run(importProductJob, jobParameters);

            // ✅ FIX 2: Используем mapToLong + sum() для long-значений
            long processed = execution.getStepExecutions()
                    .stream()
                    .mapToLong(step -> step.getReadCount() + step.getWriteCount())
                    .sum();

            return ResponseEntity.ok(
                    JobLaunchResponse.success(execution.getId().toString(), (int) processed));

        } catch (JobExecutionAlreadyRunningException e) {
            return ResponseEntity.status(409).body(
                    JobLaunchResponse.error("N/A", "Job is already running"));
        } catch (JobRestartException | JobInstanceAlreadyCompleteException e) {
            return ResponseEntity.badRequest().body(
                    JobLaunchResponse.error("N/A", e.getMessage()));
        } catch (JobParametersInvalidException e) {
            return ResponseEntity.badRequest().body(
                    JobLaunchResponse.error("N/A", "Invalid parameters: " + e.getMessage()));
        }
    }
}