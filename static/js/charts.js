// Chart utilities for InterviewBuddy

function createPerformanceChart(scores) {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;
    
    const excellent = scores.filter(s => s >= 8).length;
    const good = scores.filter(s => s >= 6 && s < 8).length;
    const needsWork = scores.filter(s => s < 6).length;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Excellent (8-10)', 'Good (6-8)', 'Needs Work (0-6)'],
            datasets: [{
                data: [excellent, good, needsWork],
                backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                borderWidth: 0,
                hoverBorderWidth: 2,
                hoverBorderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000
            }
        }
    });
}

function createScoreProgressionChart(progressionData) {
    const ctx = document.getElementById('scoreProgressionChart');
    if (!ctx || !progressionData || progressionData.length === 0) return;
    
    const labels = progressionData.map(item => item.date);
    const scores = progressionData.map(item => item.score);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score',
                data: scores,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#0d6efd',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#0d6efd',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Score'
                    },
                    min: 0,
                    max: 10,
                    ticks: {
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

function createCategoryPerformanceChart(categoryData) {
    const ctx = document.getElementById('categoryPerformanceChart');
    if (!ctx || !categoryData) return;
    
    const categories = Object.keys(categoryData);
    const scores = Object.values(categoryData);
    
    // Generate colors for each category
    const colors = generateColors(categories.length);
    
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Performance',
                data: scores,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.2)',
                borderWidth: 2,
                pointBackgroundColor: '#0d6efd',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                r: {
                    angleLines: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    pointLabels: {
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        beginAtZero: true,
                        max: 10,
                        stepSize: 2,
                        display: false
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutCubic'
            }
        }
    });
}

function createDomainDistributionChart(domainData) {
    const ctx = document.getElementById('domainChart');
    if (!ctx || !domainData) return;
    
    const domains = Object.keys(domainData);
    const counts = Object.values(domainData);
    const colors = generateColors(domains.length);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: domains,
            datasets: [{
                label: 'Interviews',
                data: counts,
                backgroundColor: colors,
                borderColor: colors.map(color => color.replace('0.8', '1')),
                borderWidth: 1,
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${context.label}: ${value} interviews (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutBounce'
            }
        }
    });
}

function createScoreDistributionChart(scores) {
    const ctx = document.getElementById('scoreDistributionChart');
    if (!ctx || !scores || scores.length === 0) return;
    
    // Create score ranges
    const ranges = ['0-2', '2-4', '4-6', '6-8', '8-10'];
    const distribution = [0, 0, 0, 0, 0];
    
    scores.forEach(score => {
        if (score >= 0 && score < 2) distribution[0]++;
        else if (score >= 2 && score < 4) distribution[1]++;
        else if (score >= 4 && score < 6) distribution[2]++;
        else if (score >= 6 && score < 8) distribution[3]++;
        else if (score >= 8 && score <= 10) distribution[4]++;
    });
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ranges,
            datasets: [{
                label: 'Number of Interviews',
                data: distribution,
                backgroundColor: [
                    'rgba(220, 53, 69, 0.8)',   // 0-2: Red
                    'rgba(255, 193, 7, 0.8)',   // 2-4: Yellow
                    'rgba(255, 152, 0, 0.8)',   // 4-6: Orange
                    'rgba(13, 202, 240, 0.8)',  // 6-8: Light Blue
                    'rgba(25, 135, 84, 0.8)'    // 8-10: Green
                ],
                borderColor: [
                    'rgba(220, 53, 69, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(255, 152, 0, 1)',
                    'rgba(13, 202, 240, 1)',
                    'rgba(25, 135, 84, 1)'
                ],
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return `Score Range: ${context[0].label}`;
                        },
                        label: function(context) {
                            const value = context.parsed.y;
                            return `${value} interview${value !== 1 ? 's' : ''}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Score Range'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Number of Interviews'
                    },
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            animation: {
                duration: 1200,
                easing: 'easeOutQuart'
            }
        }
    });
}

function generateColors(count) {
    const colors = [
        'rgba(13, 110, 253, 0.8)',   // Primary Blue
        'rgba(25, 135, 84, 0.8)',    // Success Green
        'rgba(255, 193, 7, 0.8)',    // Warning Yellow
        'rgba(220, 53, 69, 0.8)',    // Danger Red
        'rgba(13, 202, 240, 0.8)',   // Info Cyan
        'rgba(111, 66, 193, 0.8)',   // Purple
        'rgba(255, 152, 0, 0.8)',    // Orange
        'rgba(32, 201, 151, 0.8)',   // Teal
        'rgba(255, 87, 87, 0.8)',    // Light Red
        'rgba(72, 219, 251, 0.8)'    // Light Blue
    ];
    
    if (count <= colors.length) {
        return colors.slice(0, count);
    }
    
    // Generate additional colors if needed
    const additionalColors = [];
    for (let i = colors.length; i < count; i++) {
        const hue = (i * 360 / count) % 360;
        additionalColors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
    }
    
    return [...colors, ...additionalColors];
}

function updateChart(chart, newData) {
    if (!chart || !newData) return;
    
    chart.data = newData;
    chart.update('active');
}

function destroyChart(chartInstance) {
    if (chartInstance) {
        chartInstance.destroy();
    }
}

// Animation helpers
function animateValue(element, start, end, duration = 1000) {
    if (!element) return;
    
    const startTime = performance.now();
    const difference = end - start;
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease out)
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = start + (difference * easeOut);
        
        element.textContent = Math.round(current);
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    
    requestAnimationFrame(updateValue);
}

function animateScoreCircle(element, score, maxScore = 10) {
    if (!element) return;
    
    const percentage = (score / maxScore) * 100;
    const degrees = (percentage / 100) * 360;
    
    element.style.setProperty('--score-angle', `${degrees}deg`);
    
    // Animate the number
    const scoreText = element.querySelector('.score-text');
    if (scoreText) {
        animateValue(scoreText, 0, score);
    }
}

// Export chart functions
window.ChartUtils = {
    createPerformanceChart,
    createScoreProgressionChart,
    createCategoryPerformanceChart,
    createDomainDistributionChart,
    createScoreDistributionChart,
    generateColors,
    updateChart,
    destroyChart,
    animateValue,
    animateScoreCircle
};
