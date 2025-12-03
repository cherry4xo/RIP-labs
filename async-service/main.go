package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"time"
)

// RiskCalculationRequest структура для входящего запроса
type RiskCalculationRequest struct {
	ReportID   int                 `json:"report_id"`
	Components []AssessmentComponent `json:"components"`
}

// AssessmentComponent структура для компонента отчета
type AssessmentComponent struct {
	ProtectionLevel string `json:"protection_level"`
	ImpactLevel     int    `json:"impact_level"`
}

// RiskCalculationResponse структура для ответа
type RiskCalculationResponse struct {
	ReportID  int    `json:"report_id"`
	RiskScore int    `json:"risk_score"`
	Status    string `json:"status"`
}

const (
	API_TOKEN = "lab8secret"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/calculate-risk", calculateRiskHandler)
	http.HandleFunc("/health", healthHandler)

	log.Printf("Starting async service on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func calculateRiskHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req RiskCalculationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	log.Printf("Received risk calculation request for report ID: %d", req.ReportID)

	// Отправляем немедленный ответ что запрос принят
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "accepted",
		"message": "Risk calculation started",
	})

	// Запускаем асинхронную обработку в отдельной горутине
	go processRiskCalculation(req)
}

func processRiskCalculation(req RiskCalculationRequest) {
	// Задержка 5-10 секунд
	delay := 5 + rand.Intn(6) // 5 + [0-5] = [5-10]
	log.Printf("Processing report %d, will complete in %d seconds", req.ReportID, delay)
	time.Sleep(time.Duration(delay) * time.Second)

	// Вычисляем risk_score по алгоритму из Python
	protectionToLikelihood := map[string]int{
		"none":  3,
		"basic": 2,
		"full":  1,
	}

	maxRiskScore := 0
	for _, component := range req.Components {
		likelihood := protectionToLikelihood[component.ProtectionLevel]
		if likelihood == 0 {
			likelihood = 3 // default
		}
		impact := component.ImpactLevel
		riskScore := likelihood * impact
		if riskScore > maxRiskScore {
			maxRiskScore = riskScore
		}
	}

	// Добавляем элемент случайности - можем увеличить risk_score на 0-2
	randomBonus := rand.Intn(3)
	finalRiskScore := maxRiskScore + randomBonus

	log.Printf("Calculated risk_score for report %d: %d (base: %d, bonus: %d)",
		req.ReportID, finalRiskScore, maxRiskScore, randomBonus)

	// Отправляем результат обратно в основной сервис
	sendResultToMainService(req.ReportID, finalRiskScore)
}

func sendResultToMainService(reportID int, riskScore int) {
	mainServiceURL := os.Getenv("MAIN_SERVICE_URL")
	if mainServiceURL == "" {
		mainServiceURL = "http://localhost:8000"
	}

	url := fmt.Sprintf("%s/api/reports/%d/risk-result", mainServiceURL, reportID)

	response := RiskCalculationResponse{
		ReportID:  reportID,
		RiskScore: riskScore,
		Status:    "success",
	}

	jsonData, err := json.Marshal(response)
	if err != nil {
		log.Printf("Error marshaling response: %v", err)
		return
	}

	req, err := http.NewRequest(http.MethodPut, url, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Token", API_TOKEN)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error sending result to main service: %v", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		log.Printf("Successfully sent risk_score %d for report %d to main service", riskScore, reportID)
	} else {
		log.Printf("Failed to send result to main service, status: %d", resp.StatusCode)
	}
}
