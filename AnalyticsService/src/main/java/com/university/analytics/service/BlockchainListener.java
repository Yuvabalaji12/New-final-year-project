package com.university.analytics.service;

import com.university.analytics.model.AnalyticsRecord;
import com.university.analytics.repository.AnalyticsRepository;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.methods.request.EthFilter;
import org.web3j.protocol.core.DefaultBlockParameterName;
import org.web3j.protocol.http.HttpService;
import java.time.LocalDateTime;

@Service
public class BlockchainListener {

    @Value("${blockchain.node.url}")
    private String nodeUrl;

    @Value("${blockchain.contract.address}")
    private String contractAddress;

    @Autowired
    private AnalyticsRepository analyticsRepository;

    private Web3j web3j;

    @PostConstruct
    public void init() {
        new Thread(() -> {
            System.out.println("=========================================");
            System.out.println("INITIALIZING BLOCKCHAIN LISTENER (ASYNC)");
            System.out.println("=========================================");
            try {
                // Give Spring a second to fully start
                Thread.sleep(2000);
                web3j = Web3j.build(new HttpService(nodeUrl));
                String version = web3j.web3ClientVersion().send().getWeb3ClientVersion();
                System.out.println("Successfully connected to Ganache! Version: " + version);
                listenToEvents();
            } catch (Exception e) {
                System.err.println("ASYNC INITIALIZATION FAILED: " + e.getMessage());
                e.printStackTrace();
            }
        }).start();
    }

    private void listenToEvents() {
        System.out.println("Starting Final Stable Listener on: " + contractAddress);
        String eventSignature = "0x3ed6146dabe95f3b883594c16a4f21db70a04da289895cbfd3affd1770ad0a9d";
        
        java.math.BigInteger lastBlock = java.math.BigInteger.ZERO;

        while (true) {
            try {
                java.math.BigInteger latest = web3j.ethBlockNumber().send().getBlockNumber();
                if (lastBlock.equals(java.math.BigInteger.ZERO)) {
                    lastBlock = latest.subtract(java.math.BigInteger.valueOf(50));
                    if (lastBlock.compareTo(java.math.BigInteger.ZERO) < 0) lastBlock = java.math.BigInteger.ZERO;
                }

                if (latest.compareTo(lastBlock) >= 0) {
                    org.web3j.protocol.core.methods.request.EthFilter filter = new org.web3j.protocol.core.methods.request.EthFilter(
                        new org.web3j.protocol.core.DefaultBlockParameterNumber(lastBlock),
                        new org.web3j.protocol.core.DefaultBlockParameterNumber(latest),
                        contractAddress
                    );
                    filter.addSingleTopic(eventSignature);

                    java.util.List<org.web3j.protocol.core.methods.response.EthLog.LogResult> logs = web3j.ethGetLogs(filter).send().getLogs();
                    if (logs != null) {
                        for (org.web3j.protocol.core.methods.response.EthLog.LogResult res : logs) {
                            processLog((org.web3j.protocol.core.methods.response.Log) res.get());
                        }
                    }
                    lastBlock = latest.add(java.math.BigInteger.ONE);
                }
                System.out.println("... Listener Heartbeat (Block " + latest + ") ...");
                Thread.sleep(5000);
            } catch (Exception e) {
                System.err.println("Listener Loop Error: " + e.getMessage());
                try { Thread.sleep(5000); } catch (InterruptedException ex) { break; }
            }
        }
    }

    private void processLog(org.web3j.protocol.core.methods.response.Log log) {
        try {
            String data = log.getData();
            if (data == null || data.length() < 130) return;
            
            // Stable Hex to String decoding (skipping 0x and first 128 chars of offset/length)
            String hex = data.startsWith("0x") ? data.substring(130) : data.substring(128);
            StringBuilder output = new StringBuilder();
            for (int i = 0; i < hex.length() - 1; i += 2) {
                try {
                    int v = Integer.parseInt(hex.substring(i, i + 2), 16);
                    if (v == 0) break; // Null terminator
                    output.append((char) v);
                } catch (Exception e) { break; }
            }
            
            String[] lines = output.toString().trim().split("\\n");
            for (String line : lines) {
                line = line.trim();
                if (line.isEmpty()) continue;
                System.out.println("[ANALYTICS] Processing line: " + line);
                
                String[] p = line.split("#");
                if (p.length >= 7) {
                    String signature = p[6];
                    if (analyticsRepository.findByDigitalSignature(signature).isEmpty()) {
                        AnalyticsRecord record = new AnalyticsRecord(p[0], p[2], signature, java.time.LocalDateTime.now());
                        analyticsRepository.save(record);
                        System.out.println(">>> DATA PERSISTED SUCCESSFULLY: " + p[0]);
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("Log processing error: " + e.getMessage());
        }
    }
}
