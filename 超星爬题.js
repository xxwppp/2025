// 当前脚本来自于http://script.345yun.cn脚本库下载！
// ==UserScript==
// @name         超星学习通自测作业考试题目解析
// @namespace    自测考试作业题目采集
// @version      2.3.0
// @description  一键解析自测考试题目，智能识别题型；解析后可导出 CSV/Excel/Json 到本地。
// @author       Jason7187
// @match        *://*.chaoxing.com/mooc-ans/mooc2/work/view*
// @match        *://*.chaoxing.com/exam-ans/exam/*
// @grant        GM_registerMenuCommand
// @grant        GM_notification
// @grant        GM_xmlhttpRequest
// @connect      api.awk618.cn
// @source       https://github.com/Jason7187/chaoxing
// @icon         https://maxpcimg.online/i/2025/03/28/67e57f6648b39.png
// @require      https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js
// ==/UserScript==

/* global XLSX */

(function () {
    'use strict';

    // ================= 全局配置 =================
    const CONFIG = {
        CLOUD_API: '', // 留空表示不使用云端API，如需使用请填写有效API地址
        API_KEY: '', // 留空表示不使用API密钥，如需使用请填写有效密钥
        DELAY_INIT: 2000,
        ANSWER_SPLITTER: '###',
        OPTION_SPLITTER: '|',
        PREVIEW_LIMIT: 100,
        HOTKEYS: {
            SHOW: 'ArrowRight',
            HIDE: 'ArrowLeft'
        },
        RETRY_COUNT: 3,        // 网络请求重试次数
        RETRY_DELAY: 2000,     // 网络请求重试延迟(ms)
        BATCH_PARSE_SIZE: 20,  // 批量解析时每批次的数量
        COLLECT_WRONG_ANSWERS: false, // 是否收集错题
    };
    
    let currentData = [];
    let wrongAnswers = []; // 存储错题
    let parserErrors = []; // 解析错误记录

    // ================= 核心解析模块 =================
    class CXParser {
        static async parseAll() {
            const { courseName, courseId } = this.getCourseInfo();
            const containers = Array.from(document.querySelectorAll('.aiArea'));
            parserErrors = []; // 清空错误记录
            
            // 分批处理以提高性能
            const results = [];
            const totalBatches = Math.ceil(containers.length / CONFIG.BATCH_PARSE_SIZE);
            
            // 初始化进度提示
            UI.showProgressIndicator(0, containers.length);
            
            for (let i = 0; i < totalBatches; i++) {
                const start = i * CONFIG.BATCH_PARSE_SIZE;
                const end = Math.min(start + CONFIG.BATCH_PARSE_SIZE, containers.length);
                const batch = containers.slice(start, end);
                
                const batchResults = batch.map(container => {
                    try {
                        const type = this.parseType(container);
                        const question = this.parseQuestion(container);
                        const options = this.parseOptions(container);
                        const answer = this.parseAnswer(container, type) || this.extractHiddenAnswer(container);
                        const score = this.parseScore(container);
                        const isWrong = this.checkIfWrong(container);
                        const difficulty = this.estimateDifficulty(container, score);
                        
                        // 如果开启了收集错题且题目回答错误
                        if (CONFIG.COLLECT_WRONG_ANSWERS && isWrong) {
                            wrongAnswers.push({
                                courseName, courseId, type, question, options, answer, score, difficulty
                            });
                        }
                        
                        return {
                            courseName,
                            courseId,
                            type,
                            question,
                            options,
                            answer,
                            score,
                            difficulty,
                            isWrong
                        };
                    } catch (error) {
                        // 记录解析失败的题目
                        parserErrors.push({
                            container,
                            error: error.message || '未知错误'
                        });
                        return null;
                    }
                }).filter(item => item && item.answer);
                
                results.push(...batchResults);
                
                // 更新进度
                UI.updateProgressIndicator(end, containers.length);
                
                // 异步处理，避免界面卡顿
                await new Promise(resolve => setTimeout(resolve, 0));
            }
            
            UI.hideProgressIndicator();
            
            return results;
        }

        static getCourseInfo() {
            return {
                courseName: document.querySelector('h2.mark_title')?.textContent.trim() || '未知课程',
                courseId: new URLSearchParams(location.search).get('courseId') || '未知ID'
            };
        }

        static parseType(container) {
            const raw = container.querySelector('.colorShallow')?.textContent?.replace(/\u00A0/g, ' ').trim() || '';
            let clean = raw
                .replace(/[([（【{<]/g, '')
                .replace(/[\])）】}>]/g, '')
                .replace(/([.·。:，,]?\s*)(共|满分)?\s*\d+\.?\d*\s*分?/g, '')
                .replace(/[.·。:，,]\s*分/g, '')
                .replace(/\s*分/g, '')
                .replace(/[\s\u3000.,。·:，、]/g, '')
                .trim();

            const map = {
                '单选': '单选题',
                '单项选择题': '单选题',
                '选择题A型': '单选题',
                '多选': '多选题',
                '多项选择题': '多选题',
                '判断': '判断题',
                '判断题': '判断题',
                '填空': '填空题',
                '简答': '简答题',
                '名词解释': '名词解释',
                '分析': '分析题',
                '问答': '问答题',
                '综合': '综合题',
            };

            for (const [key, value] of Object.entries(map)) {
                if (clean.includes(key)) return value;
            }
            return clean;
        }

        static isMultipleChoice(container) {
            const type = this.parseType(container);
            return type.includes('多选');
        }

        static parseQuestion(container) {
            const content = container.querySelector('.qtContent') || container.querySelector('.mark_name');
            if (!content) return '';
            return this.extractTextWithImgs(content);
        }

        static parseOptions(container) {
            const optionElements = container.querySelectorAll('.mark_letter li, .stem_answer > div');
            return Array.from(optionElements).map((optionDiv, idx) => {
                const letter = String.fromCharCode(65 + idx);
                let text = this.extractTextWithImgs(optionDiv);
                text = text.replace(/^[A-Z]\s*[．.。]?\s*/, '');
                return `${letter}. ${text}`;
            }).join(' | ');
        }

        static parseAnswer(container, type) {
            if (type === '填空题') {
                const rightAnswerElements = container.querySelectorAll('.rightAnswerContent');
                if (!rightAnswerElements.length) return '';
                const answers = Array.from(rightAnswerElements).map(el => {
                    const rawText = el.textContent.trim().replace(/^\(\d+\)\s*/, '');
                    const parts = rawText.split(/[,，、/\s]+/).filter(Boolean);
                    return [...new Set(parts)].join('；');
                });
                return answers.join('\n');
            }

            let correctAnswer = this.extractRightAnswer(container);
            if (!correctAnswer) {
                if (this.isMultipleChoice(container)) {
                    correctAnswer = this.extractMultipleChoiceAnswer(container) || this.extractHiddenAnswer(container);
                } else {
                    correctAnswer = this.extractHiddenAnswer(container);
                }
                if (!correctAnswer) {
                    const isCorrect = container.querySelector('.marking_dui');
                    const studentAnswer = container.querySelector('.stuAnswerContent')?.textContent.trim();
                    if (isCorrect && studentAnswer) {
                        correctAnswer = studentAnswer;
                    }
                }
            }

            if (this.isOptionLetter(correctAnswer)) {
                const optionsMap = this.buildOptionsMap(container);
                correctAnswer = this.mapAnswerToOptions(correctAnswer, optionsMap);
            }

            return this.cleanAnswerText(correctAnswer);
        }

        static extractMultipleChoiceAnswer(container) {
            const el = container.querySelector('.rightAnswerContent');
            return el ? el.textContent.trim() : '';
        }

        static isOptionLetter(answer) {
            return /^[A-Za-z]+$/.test(answer);
        }

        static buildOptionsMap(container) {
            const optionElements = container.querySelectorAll('.mark_letter li, .stem_answer > div');
            return Array.from(optionElements).reduce((map, el, idx) => {
                const letter = String.fromCharCode(65 + idx);
                let text = this.extractTextWithImgs(el);
                text = text.replace(/^[A-Z]\s*[．.。]?\s*/, '').trim();
                map[letter] = text;
                return map;
            }, {});
        }

        static mapAnswerToOptions(answer, optionsMap) {
            return answer.split('').map(letter => {
                return optionsMap[letter.toUpperCase()] || letter;
            }).join('###');
        }

        static cleanAnswerText(answer) {
            return answer.split('###')
                .map(item => item.trim())
                .map(item => item.replace(/^["']+|["']+$/g, ''))
                .join('###');
        }

        static extractRightAnswer(container) {
            const rightAnswerElement = container.querySelector('.rightAnswerContent');
            return rightAnswerElement ? rightAnswerElement.textContent.trim() : '';
        }

        static extractHiddenAnswer(container) {
            const hiddenAnswerElement = container.querySelector('.element-invisible-hidden');
            if (!hiddenAnswerElement) return '';
            let answerText = hiddenAnswerElement.textContent.trim()
                .replace(/^:/, '')
                .replace(/['"]+/g, '')
                .replace(/;$/, '');

            if (this.isMultipleChoice(container)) {
                answerText = answerText.replace(/;/g, '###');
            }
            return answerText.trim();
        }

        static parseScore(container) {
            const scoreElement = container.querySelector('.totalScore i');
            return scoreElement ? parseFloat(scoreElement.textContent.trim()) : null;
        }

        static extractTextWithImgs(element) {
            const cloned = element.cloneNode(true);
            const imgs = cloned.querySelectorAll('img');
            imgs.forEach(img => {
                const url = img.getAttribute('src') || img.getAttribute('data-original') || '';
                const textNode = document.createTextNode(url);
                img.parentNode.replaceChild(textNode, img);
            });

            let text = cloned.textContent
                .replace(/\u00a0/g, ' ')
                .replace(/\r?\n/g, ' ')
                .replace(/\s+/g, ' ')
                .trim();

            return text;
        }
        
        // 新增：检查题目是否错误
        static checkIfWrong(container) {
            const isWrong = container.querySelector('.marking_cuo');
            return !!isWrong;
        }
        
        // 新增：估计题目难度
        static estimateDifficulty(container, score) {
            // 根据分值和其他特征估计难度
            if (!score) return '未知';
            
            // 检查是否有同学做错的痕迹
            const wrongMarks = container.querySelectorAll('.marking_cuo');
            const totalMarks = container.querySelectorAll('.marking_cuo, .marking_dui');
            
            if (totalMarks.length === 0) return '未知';
            
            const wrongRate = wrongMarks.length / totalMarks.length;
            
            // 根据分值和错误率判断难度
            if (score >= 5) {
                if (wrongRate > 0.5) return '困难';
                if (wrongRate > 0.3) return '中等';
                return '简单';
            } else {
                if (wrongRate > 0.4) return '中等';
                return '简单';
            }
        }
    }

    // ================= 数据导出 & 上传模块 =================
    class DataExporter {
        static async serializeForUpload(data) {
            return JSON.stringify({
                meta: {
                    courseId: CXParser.getCourseInfo().courseId,
                    courseName: CXParser.getCourseInfo().courseName,
                    exportDate: new Date().toISOString()
                },
                questions: data.map(item => ({
                    courseName: item.courseName,
                    courseId: item.courseId,
                    type: item.type,
                    question: item.question,
                    options: item.options.split(CONFIG.OPTION_SPLITTER),
                    answer: item.answer,
                    difficulty: item.difficulty
                }))
            });
        }

        static async uploadToCloud(data) {
            return new Promise((resolve, reject) => {
                const uploadWithRetry = (retryCount = 0) => {
                    UI.showLoading('正在上传数据...');
                    GM_xmlhttpRequest({
                        method: 'POST',
                        url: CONFIG.CLOUD_API,
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': CONFIG.API_KEY
                        },
                        data: this.serializeForUpload(data),
                        timeout: 10000,
                        onload: (response) => {
                            UI.hideLoading();
                            if (response.status >= 200 && response.status < 300) {
                                UI.showNotification('上传成功！', 'success');
                                resolve(response);
                            } else {
                                if (retryCount < CONFIG.RETRY_COUNT) {
                                    UI.showNotification(`上传失败，${CONFIG.RETRY_DELAY/1000}秒后重试...`, 'warning');
                                    setTimeout(() => uploadWithRetry(retryCount + 1), CONFIG.RETRY_DELAY);
                                } else {
                                    UI.showNotification('上传失败，已达到最大重试次数', 'error');
                                    reject(new Error(`上传失败: ${response.status} ${response.statusText}`));
                                }
                            }
                        },
                        onerror: (error) => {
                            UI.hideLoading();
                            if (retryCount < CONFIG.RETRY_COUNT) {
                                UI.showNotification(`网络错误，${CONFIG.RETRY_DELAY/1000}秒后重试...`, 'warning');
                                setTimeout(() => uploadWithRetry(retryCount + 1), CONFIG.RETRY_DELAY);
                            } else {
                                UI.showNotification('网络错误，已达到最大重试次数', 'error');
                                reject(error);
                            }
                        }
                    });
                };
                
                uploadWithRetry();
            });
        }

        static async exportCSV(data) {
            UI.showLoading('正在导出CSV...');
            
            // 使用Web Worker处理大量数据，避免主线程阻塞
            const worker = this.createWorker((data) => {
                const escapeCSV = text => /[\n\t"]/.test(text)
                    ? `"${text.replace(/"/g, '""')}"`
                    : text;
                    
                const headers = ['课程名', '课程ID', '题型', '题目', '选项', '答案', '分值', '难度', '是否错题'];
                const rows = [headers.join('\t')];
                
                data.forEach(item => {
                    const row = [
                        item.courseName, 
                        item.courseId, 
                        item.type,
                        item.question, 
                        item.options, 
                        item.answer, 
                        item.score || '', 
                        item.difficulty || '未知',
                        item.isWrong ? '是' : '否'
                    ].map(escapeCSV);
                    
                    rows.push(row.join('\t'));
                });
                
                return "\uFEFF" + rows.join('\n'); // 添加BOM标记确保UTF-8编码
            });
            
            worker.onmessage = (e) => {
                this.downloadFile(e.data, `${this.getFileName()}.csv`, 'text/csv;charset=utf-8;');
                worker.terminate();
                UI.hideLoading();
            };
            
            worker.postMessage(data);
        }

        static async exportExcel(data) {
            UI.showLoading('正在导出Excel...');
            
            try {
                // 使用Web Worker处理Excel导出，避免界面卡顿
                const worker = this.createWorker((data) => {
                    // 注意：Web Worker中不能直接使用XLSX，需要importScripts
                    // 这里假设已在主线程中处理好数据格式
                    return data.map(item => ({
                        '课程名': item.courseName,
                        '课程ID': item.courseId,
                        '题型': item.type,
                        '题目': item.question,
                        '选项': item.options,
                        '答案': item.answer,
                        '分值': item.score || '',
                        '难度': item.difficulty || '未知',
                        '是否错题': item.isWrong ? '是' : '否'
                    }));
                });
                
                worker.onmessage = (e) => {
                    const ws = XLSX.utils.json_to_sheet(e.data);
                    const wb = XLSX.utils.book_new();
                    XLSX.utils.book_append_sheet(wb, ws, '题目数据');
                    
                    // 针对Excel导出的优化，减少内存使用
                    XLSX.writeFile(wb, `${this.getFileName()}.xlsx`, {
                        compression: true,
                        bookType: 'xlsx'
                    });
                    
                    worker.terminate();
                    UI.hideLoading();
                };
                
                worker.postMessage(data);
            } catch (error) {
                console.error('导出Excel失败:', error);
                UI.showNotification('导出Excel失败: ' + error.message, 'error');
                UI.hideLoading();
            }
        }

        static async exportJSON(data) {
            UI.showLoading('正在导出JSON...');
            
            const worker = this.createWorker((data) => {
                return JSON.stringify({
                    meta: {
                        courseId: data[0]?.courseId || '未知ID',
                        courseName: data[0]?.courseName || '未知课程',
                        exportDate: new Date().toISOString()
                    },
                    questions: data.map(item => ({
                        ...item,
                        options: item.options.split(' | ')
                    }))
                }, null, 2);
            });
            
            worker.onmessage = (e) => {
                this.downloadFile(e.data, `${this.getFileName()}.json`, 'application/json;charset=utf-8;');
                worker.terminate();
                UI.hideLoading();
            };
            
            worker.postMessage(data);
        }
        
        // 导出错题集
        static exportWrongAnswers() {
            if (wrongAnswers.length === 0) {
                UI.showNotification('没有收集到错题', 'warning');
                return;
            }
            
            this.exportJSON(wrongAnswers);
            UI.showNotification(`成功导出${wrongAnswers.length}道错题`, 'success');
        }
        
        static createWorker(fn) {
            const blob = new Blob([
                `self.onmessage = function(e) { 
                    const result = (${fn.toString()})(e.data);
                    self.postMessage(result);
                }`
            ], { type: 'application/javascript' });
            
            return new Worker(URL.createObjectURL(blob));
        }

        static downloadFile(content, filename, mime) {
            const blob = new Blob([content], { type: mime });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
        }

        static getFileName() {
            const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
            return `${CXParser.getCourseInfo().courseName}_${date}`;
        }
        
        // 题目反馈功能
        static async submitFeedback(questionData, feedback) {
            if (!CONFIG.CLOUD_API) {
                UI.showNotification('未配置云端API，无法提交反馈', 'error');
                return;
            }
            
            return new Promise((resolve, reject) => {
                const submitWithRetry = (retryCount = 0) => {
                    UI.showLoading('正在提交反馈...');
                    GM_xmlhttpRequest({
                        method: 'POST',
                        url: `${CONFIG.CLOUD_API}/feedback`,
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': CONFIG.API_KEY
                        },
                        data: JSON.stringify({
                            questionData,
                            feedback,
                            submittedAt: new Date().toISOString()
                        }),
                        timeout: 10000,
                        onload: (response) => {
                            UI.hideLoading();
                            if (response.status >= 200 && response.status < 300) {
                                UI.showNotification('反馈提交成功！', 'success');
                                resolve(response);
                            } else {
                                if (retryCount < CONFIG.RETRY_COUNT) {
                                    UI.showNotification(`提交失败，${CONFIG.RETRY_DELAY/1000}秒后重试...`, 'warning');
                                    setTimeout(() => submitWithRetry(retryCount + 1), CONFIG.RETRY_DELAY);
                                } else {
                                    UI.showNotification('提交失败，已达到最大重试次数', 'error');
                                    reject(new Error(`提交失败: ${response.status} ${response.statusText}`));
                                }
                            }
                        },
                        onerror: (error) => {
                            UI.hideLoading();
                            if (retryCount < CONFIG.RETRY_COUNT) {
                                UI.showNotification(`网络错误，${CONFIG.RETRY_DELAY/1000}秒后重试...`, 'warning');
                                setTimeout(() => submitWithRetry(retryCount + 1), CONFIG.RETRY_DELAY);
                            } else {
                                UI.showNotification('网络错误，已达到最大重试次数', 'error');
                                reject(error);
                            }
                        }
                    });
                };
                
                submitWithRetry();
            });
        }
    }
    
    // ================= UI组件类 =================
    class UI {
        static showNotification(message, type = 'info') {
            GM_notification({
                text: message,
                title: '超星题目解析',
                timeout: 3000
            });
            
            // 同时在界面上显示通知
            const notification = document.createElement('div');
            notification.className = `cx-notification cx-${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            // 添加动画效果
            setTimeout(() => notification.classList.add('show'), 10);
            
            // 自动移除
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
        
        static showLoading(message) {
            let loading = document.getElementById('cx-loading');
            if (!loading) {
                loading = document.createElement('div');
                loading.id = 'cx-loading';
                loading.innerHTML = `
                    <div class="cx-spinner"></div>
                    <div class="cx-loading-text"></div>
                `;
                document.body.appendChild(loading);
            }
            
            loading.querySelector('.cx-loading-text').textContent = message;
            loading.classList.add('show');
        }
        
        static hideLoading() {
            const loading = document.getElementById('cx-loading');
            if (loading) {
                loading.classList.remove('show');
            }
        }
        
        static showProgressIndicator(current, total) {
            let progress = document.getElementById('cx-progress');
            if (!progress) {
                progress = document.createElement('div');
                progress.id = 'cx-progress';
                progress.innerHTML = `
                    <div class="cx-progress-bar">
                        <div class="cx-progress-fill"></div>
                    </div>
                    <div class="cx-progress-text">0%</div>
                `;
                document.body.appendChild(progress);
            }
            
            this.updateProgressIndicator(current, total);
            progress.classList.add('show');
        }
        
        static updateProgressIndicator(current, total) {
            const progress = document.getElementById('cx-progress');
            if (!progress) return;
            
            const percent = Math.round((current / total) * 100);
            progress.querySelector('.cx-progress-fill').style.width = `${percent}%`;
            progress.querySelector('.cx-progress-text').textContent = `${percent}% (${current}/${total})`;
        }
        
        static hideProgressIndicator() {
            const progress = document.getElementById('cx-progress');
            if (progress) {
                setTimeout(() => {
                    progress.classList.remove('show');
                }, 1000);
            }
        }
        
        static showErrorDetails() {
            if (parserErrors.length === 0) {
                this.showNotification('没有解析错误', 'info');
                return;
            }
            
            const modal = document.createElement('div');
            modal.className = 'cx-modal';
            modal.innerHTML = `
                <div class="cx-modal-content">
                    <div class="cx-modal-header">
                        <h3>解析错误详情 (共${parserErrors.length}个)</h3>
                        <button class="cx-close-btn">&times;</button>
                    </div>
                    <div class="cx-modal-body">
                        <ul class="cx-error-list">
                            ${parserErrors.map((err, idx) => `
                                <li>
                                    <strong>错误 #${idx + 1}:</strong> ${err.error}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            modal.querySelector('.cx-close-btn').onclick = () => modal.remove();
            
            // 添加淡入效果
            setTimeout(() => modal.classList.add('show'), 10);
        }
        
        static createFeedbackUI(question) {
            const modal = document.createElement('div');
            modal.className = 'cx-modal';
            modal.innerHTML = `
                <div class="cx-modal-content">
                    <div class="cx-modal-header">
                        <h3>提交题目反馈</h3>
                        <button class="cx-close-btn">&times;</button>
                    </div>
                    <div class="cx-modal-body">
                        <div class="cx-feedback-question">
                            <strong>题目:</strong> ${question.question}
                        </div>
                        <div class="cx-feedback-answer">
                            <strong>当前答案:</strong> ${question.answer}
                        </div>
                        <div class="cx-feedback-form">
                            <label>
                                <input type="radio" name="feedback-type" value="wrong-answer" checked>
                                答案错误
                            </label>
                            <label>
                                <input type="radio" name="feedback-type" value="typo">
                                题目或选项有错别字
                            </label>
                            <label>
                                <input type="radio" name="feedback-type" value="other">
                                其他问题
                            </label>
                            <textarea class="cx-feedback-text" placeholder="请详细描述问题，如果知道正确答案请提供..."></textarea>
                            <div class="cx-feedback-actions">
                                <button class="cx-submit-btn">提交反馈</button>
                                <button class="cx-cancel-btn">取消</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 绑定事件
            modal.querySelector('.cx-close-btn').onclick = () => modal.remove();
            modal.querySelector('.cx-cancel-btn').onclick = () => modal.remove();
            
            modal.querySelector('.cx-submit-btn').onclick = async () => {
                const feedbackType = modal.querySelector('input[name="feedback-type"]:checked').value;
                const feedbackText = modal.querySelector('.cx-feedback-text').value.trim();
                
                if (!feedbackText) {
                    this.showNotification('请填写反馈内容', 'warning');
                    return;
                }
                
                try {
                    await DataExporter.submitFeedback(question, {
                        type: feedbackType,
                        content: feedbackText
                    });
                    modal.remove();
                } catch (error) {
                    console.error('提交反馈失败:', error);
                }
            };
            
            // 添加淡入效果
            setTimeout(() => modal.classList.add('show'), 10);
        }
    }

    // ================= 预览界面模块 =================
    class PreviewUI {
        static show(data) {
            this.close();
            const preview = this.createPreview(data);
            document.body.appendChild(preview);
            
            // 初始化拖拽功能
            this.initDraggable(preview);
            
            // 添加动画效果
            setTimeout(() => preview.classList.add('show'), 10);
        }

        static createPreview(data) {
            const div = document.createElement('div');
            div.id = 'cx-preview';
            div.innerHTML = `
                <div class="cx-header">
                    <div class="cx-drag-handle">
                        <h3><span class="cx-sparkle">✨</span> 成功解析 ${data.length} 道题目</h3>
                        ${parserErrors.length > 0 ? `<span class="cx-error-badge">${parserErrors.length}个解析错误</span>` : ''}
                    </div>
                    <div class="cx-header-actions">
                        <button class="cx-minimize-btn" title="最小化">-</button>
                        <button class="cx-close-btn" title="关闭">&times;</button>
                    </div>
                </div>
                <div class="cx-table-container">
                    ${this.createTable(data)}
                </div>
                <div class="cx-action-bar">
                    <div class="cx-action-group">
                        <button class="cx-export-btn csv">导出CSV</button>
                        <button class="cx-export-btn excel">导出Excel</button>
                        <button class="cx-export-btn json">导出JSON</button>
                    </div>
                    <div class="cx-action-group">
                        ${parserErrors.length > 0 ? 
                          `<button class="cx-error-btn">查看解析错误</button>` : ''}
                        ${CONFIG.COLLECT_WRONG_ANSWERS ? 
                          `<button class="cx-wrong-btn">导出错题集(${wrongAnswers.length})</button>` : ''}
                        <div class="cx-switch">
                            <label>
                                <input type="checkbox" ${CONFIG.COLLECT_WRONG_ANSWERS ? 'checked' : ''} id="toggle-wrong-answers">
                                <span class="cx-slider"></span>
                                收集错题
                            </label>
                        </div>
                    </div>
                </div>
            `;
            
            // 绑定事件
            div.querySelector('.cx-close-btn').onclick = () => this.close();
            div.querySelector('.cx-minimize-btn').onclick = () => this.minimize();
            div.querySelector('.csv').onclick = () => DataExporter.exportCSV(currentData);
            div.querySelector('.excel').onclick = () => DataExporter.exportExcel(currentData);
            div.querySelector('.json').onclick = () => DataExporter.exportJSON(currentData);
            
            const errorBtn = div.querySelector('.cx-error-btn');
            if (errorBtn) {
                errorBtn.onclick = () => UI.showErrorDetails();
            }
            
            const wrongBtn = div.querySelector('.cx-wrong-btn');
            if (wrongBtn) {
                wrongBtn.onclick = () => DataExporter.exportWrongAnswers();
            }
            
            // 绑定收集错题开关
            const toggleWrong = div.querySelector('#toggle-wrong-answers');
            if (toggleWrong) {
                toggleWrong.onchange = (e) => {
                    CONFIG.COLLECT_WRONG_ANSWERS = e.target.checked;
                    localStorage.setItem('CX_COLLECT_WRONG_ANSWERS', e.target.checked ? '1' : '0');
                    UI.showNotification(e.target.checked ? '已开启错题收集' : '已关闭错题收集', 'info');
                };
            }
            
            return div;
        }

        static createTable(data) {
            return `
                <table class="cx-table">
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>题型</th>
                            <th>难度</th>
                            <th class="cx-col-question">题目</th>
                            <th class="cx-col-options">选项</th>
                            <th class="cx-col-answer">答案</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.slice(0, CONFIG.PREVIEW_LIMIT).map((item, index) => `
                            <tr class="${item.isWrong ? 'cx-wrong-row' : ''}">
                                <td>${index + 1}</td>
                                <td>${item.type}</td>
                                <td><span class="cx-difficulty cx-difficulty-${this.getDifficultyClass(item.difficulty)}">${item.difficulty || '未知'}</span></td>
                                <td class="cx-col-question">${this.truncateText(item.question, 100)}</td>
                                <td class="cx-col-options">${this.formatOptions(item.options)}</td>
                                <td class="cx-col-answer">${this.formatAnswer(item.answer)}</td>
                                <td>
                                    <button class="cx-feedback-btn" data-index="${index}">
                                        <span class="cx-icon">✏️</span>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }

        static getDifficultyClass(difficulty) {
            switch(difficulty) {
                case '简单': return 'easy';
                case '中等': return 'medium';
                case '困难': return 'hard';
                default: return 'unknown';
            }
        }

        static truncateText(text, maxLength) {
            if (!text) return '';
            return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
        }

        static formatOptions(options) {
            if (!options) return '';
            return options.replace(/\|/g, '<br>');
        }

        static formatAnswer(answer) {
            if (!answer) return '';
            return answer.replace(/###/g, '<br>');
        }

        static initDraggable(element) {
            const handle = element.querySelector('.cx-drag-handle');
            if (!handle) return;
            
            let isDragging = false;
            let offsetX, offsetY;
            
            handle.addEventListener('mousedown', (e) => {
                isDragging = true;
                const rect = element.getBoundingClientRect();
                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;
                
                // 添加动画过渡禁用，避免拖拽时有延迟感
                element.style.transition = 'none';
                
                // 添加拖拽时的视觉效果
                element.classList.add('cx-dragging');
                
                e.preventDefault();
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                
                const x = e.clientX - offsetX;
                const y = e.clientY - offsetY;
                
                // 确保不会被拖出视口
                const maxX = window.innerWidth - element.offsetWidth;
                const maxY = window.innerHeight - element.offsetHeight;
                
                element.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
                element.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
            });
            
            document.addEventListener('mouseup', () => {
                if (!isDragging) return;
                isDragging = false;
                
                // 恢复动画过渡
                element.style.transition = '';
                
                // 移除拖拽时的视觉效果
                element.classList.remove('cx-dragging');
                
                // 保存位置到本地存储
                localStorage.setItem('CX_PREVIEW_POS', JSON.stringify({
                    left: element.style.left,
                    top: element.style.top
                }));
            });
            
            // 恢复上次保存的位置
            const savedPos = localStorage.getItem('CX_PREVIEW_POS');
            if (savedPos) {
                try {
                    const { left, top } = JSON.parse(savedPos);
                    element.style.left = left;
                    element.style.top = top;
                } catch (e) {
                    console.error('恢复预览窗口位置失败', e);
                }
            }
        }

        static minimize() {
            const preview = document.getElementById('cx-preview');
            if (preview) {
                if (preview.classList.contains('minimized')) {
                    preview.classList.remove('minimized');
                    localStorage.setItem('CX_PREVIEW_MINIMIZED', '0');
                } else {
                    preview.classList.add('minimized');
                    localStorage.setItem('CX_PREVIEW_MINIMIZED', '1');
                }
            }
        }

        static close() {
            const preview = document.getElementById('cx-preview');
            if (preview) {
                // 添加关闭动画
                preview.classList.add('cx-closing');
                
                // 等待动画结束后移除元素
                setTimeout(() => preview.remove(), 300);
            }
        }
        
        // 初始化样式
        static injectStyles() {
            if (document.getElementById('cx-preview-styles')) return;
            
            const style = document.createElement('style');
            style.id = 'cx-preview-styles';
            style.textContent = `
                #cx-preview {
                    position: fixed;
                    top: 50px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 90%;
                    max-width: 1200px;
                    max-height: 80vh;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 5px 30px rgba(0, 0, 0, 0.2);
                    z-index: 99999;
                    display: flex;
                    flex-direction: column;
                    opacity: 0;
                    transform: translateY(20px) translateX(-50%);
                    transition: opacity 0.3s ease, transform 0.3s ease;
                    overflow: hidden;
                }
                
                #cx-preview.show {
                    opacity: 1;
                    transform: translateY(0) translateX(-50%);
                }
                
                #cx-preview.minimized .cx-table-container {
                    display: none;
                }
                
                #cx-preview.minimized .cx-action-bar {
                    display: none;
                }
                
                #cx-preview.minimized {
                    width: auto;
                    max-width: 300px;
                }
                
                #cx-preview.cx-closing {
                    opacity: 0;
                    transform: translateY(20px) translateX(-50%);
                }
                
                #cx-preview.cx-dragging {
                    opacity: 0.8;
                    cursor: grabbing;
                }
                
                .cx-header {
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid #eee;
                    background: #f8f9fa;
                }
                
                .cx-drag-handle {
                    cursor: grab;
                    user-select: none;
                    flex: 1;
                }
                
                .cx-drag-handle h3 {
                    margin: 0;
                    display: inline-block;
                }
                
                .cx-header-actions {
                    display: flex;
                    gap: 10px;
                }
                
                .cx-minimize-btn, .cx-close-btn {
                    background: none;
                    border: none;
                    font-size: 18px;
                    cursor: pointer;
                    width: 28px;
                    height: 28px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background-color 0.2s;
                }
                
                .cx-minimize-btn:hover, .cx-close-btn:hover {
                    background-color: rgba(0, 0, 0, 0.1);
                }
                
                .cx-table-container {
                    flex: 1;
                    overflow: auto;
                    max-height: 60vh;
                    padding: 10px;
                }
                
                .cx-table {
                    width: 100%;
                    border-collapse: collapse;
                    table-layout: fixed;
                }
                
                .cx-table th {
                    position: sticky;
                    top: 0;
                    background: white;
                    z-index: 1;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    padding: 10px;
                    text-align: left;
                    border-bottom: 2px solid #eee;
                }
                
                .cx-table td {
                    padding: 12px 10px;
                    border-bottom: 1px solid #eee;
                    vertical-align: top;
                }
                
                .cx-table tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                
                .cx-table tr:hover {
                    background-color: #f0f7ff;
                }
                
                .cx-wrong-row {
                    background-color: #fff8f8 !important;
                }
                
                .cx-col-question {
                    width: 30%;
                }
                
                .cx-col-options {
                    width: 30%;
                }
                
                .cx-col-answer {
                    width: 20%;
                    color: #2196F3;
                    font-weight: 500;
                }
                
                .cx-action-bar {
                    padding: 15px;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    gap: 10px;
                }
                
                .cx-action-group {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                }
                
                .cx-export-btn {
                    padding: 8px 15px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.2s;
                }
                
                .csv {
                    background: #4CAF50;
                    color: white;
                }
                
                .excel {
                    background: #2196F3;
                    color: white;
                }
                
                .json {
                    background: #FF9800;
                    color: white;
                }
                
                .cx-export-btn:hover {
                    opacity: 0.9;
                    transform: translateY(-2px);
                }
                
                .cx-error-btn, .cx-wrong-btn {
                    padding: 8px 15px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    background: #f44336;
                    color: white;
                }
                
                .cx-error-badge {
                    display: inline-block;
                    padding: 2px 8px;
                    background: #f44336;
                    color: white;
                    border-radius: 10px;
                    font-size: 12px;
                    margin-left: 10px;
                }
                
                .cx-difficulty {
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                }
                
                .cx-difficulty-easy {
                    background-color: #e8f5e9;
                    color: #43a047;
                }
                
                .cx-difficulty-medium {
                    background-color: #fff3e0;
                    color: #ef6c00;
                }
                
                .cx-difficulty-hard {
                    background-color: #ffebee;
                    color: #d32f2f;
                }
                
                .cx-difficulty-unknown {
                    background-color: #f5f5f5;
                    color: #757575;
                }
                
                .cx-feedback-btn {
                    background: none;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                    padding: 5px;
                    border-radius: 5px;
                }
                
                .cx-feedback-btn:hover {
                    background: rgba(0, 0, 0, 0.05);
                }
                
                .cx-sparkle {
                    display: inline-block;
                    animation: sparkle 2s infinite;
                }
                
                @keyframes sparkle {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.2); }
                    100% { transform: scale(1); }
                }
                
                .cx-switch {
                    position: relative;
                    display: inline-block;
                }
                
                .cx-switch label {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    cursor: pointer;
                }
                
                .cx-switch input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                
                .cx-slider {
                    position: relative;
                    display: inline-block;
                    width: 40px;
                    height: 20px;
                    background-color: #ccc;
                    border-radius: 20px;
                    transition: .4s;
                }
                
                .cx-slider:before {
                    position: absolute;
                    content: "";
                    height: 16px;
                    width: 16px;
                    left: 2px;
                    bottom: 2px;
                    background-color: white;
                    border-radius: 50%;
                    transition: .4s;
                }
                
                input:checked + .cx-slider {
                    background-color: #2196F3;
                }
                
                input:checked + .cx-slider:before {
                    transform: translateX(20px);
                }
                
                /* 通知样式 */
                .cx-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    z-index: 100000;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    opacity: 0;
                    transform: translateY(-20px);
                    transition: opacity 0.3s, transform 0.3s;
                }
                
                .cx-notification.show {
                    opacity: 1;
                    transform: translateY(0);
                }
                
                .cx-info {
                    background-color: #2196F3;
                }
                
                .cx-success {
                    background-color: #4CAF50;
                }
                
                .cx-warning {
                    background-color: #FF9800;
                }
                
                .cx-error {
                    background-color: #F44336;
                }
                
                /* 加载指示器样式 */
                #cx-loading {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    z-index: 100001;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s;
                }
                
                #cx-loading.show {
                    opacity: 1;
                    visibility: visible;
                }
                
                .cx-spinner {
                    border: 5px solid rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    border-top: 5px solid white;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                }
                
                .cx-loading-text {
                    color: white;
                    margin-top: 15px;
                    font-size: 16px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                /* 进度指示器样式 */
                #cx-progress {
                    position: fixed;
                    bottom: 30px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 300px;
                    background: white;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    z-index: 100000;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s;
                }
                
                #cx-progress.show {
                    opacity: 1;
                    visibility: visible;
                }
                
                .cx-progress-bar {
                    width: 100%;
                    height: 8px;
                    background: #eee;
                    border-radius: 4px;
                    overflow: hidden;
                    margin-bottom: 8px;
                }
                
                .cx-progress-fill {
                    height: 100%;
                    background: #2196F3;
                    width: 0%;
                    transition: width 0.3s;
                }
                
                .cx-progress-text {
                    text-align: center;
                    font-size: 14px;
                    color: #666;
                }
                
                /* 模态框样式 */
                .cx-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 100002;
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.3s;
                }
                
                .cx-modal.show {
                    opacity: 1;
                    visibility: visible;
                }
                
                .cx-modal-content {
                    background: white;
                    border-radius: 8px;
                    width: 90%;
                    max-width: 600px;
                    max-height: 80vh;
                    overflow: auto;
                }
                
                .cx-modal-header {
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .cx-modal-header h3 {
                    margin: 0;
                }
                
                .cx-modal-body {
                    padding: 20px 15px;
                }
                
                .cx-error-list {
                    margin: 0;
                    padding-left: 20px;
                }
                
                .cx-error-list li {
                    margin-bottom: 10px;
                    line-height: 1.5;
                }
                
                .cx-feedback-question, .cx-feedback-answer {
                    margin-bottom: 15px;
                    padding: 10px;
                    background: #f5f5f5;
                    border-radius: 5px;
                    max-height: 100px;
                    overflow: auto;
                }
                
                .cx-feedback-form {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }
                
                .cx-feedback-form label {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .cx-feedback-text {
                    width: 100%;
                    min-height: 100px;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    resize: vertical;
                    font-family: inherit;
                    font-size: 14px;
                }
                
                .cx-feedback-actions {
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                    margin-top: 10px;
                }
                
                .cx-submit-btn, .cx-cancel-btn {
                    padding: 8px 15px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                }
                
                .cx-submit-btn {
                    background: #2196F3;
                    color: white;
                }
                
                .cx-cancel-btn {
                    background: #f5f5f5;
                    color: #333;
                }
            `;
            document.head.appendChild(style);
        }
    }

    // ================= 主控制模块 =================
    class MainController {
        static init() {
            this.initToolbar();
            this.initHotkeys();
            this.autoParseAndUpload();
            this.bindFeedbackEvents();
            
            // 注入全局样式
            PreviewUI.injectStyles();
        }

        static initToolbar() {
            const toolbar = document.createElement('div');
            toolbar.id = 'cx-toolbar';
            toolbar.innerHTML = `
                <button class="cx-parse-btn">
                    <span class="cx-sparkle">✨</span> 开始解析
                </button>
            `;
            
            // 使工具栏可拖动
            this.makeToolbarDraggable(toolbar);
            
            toolbar.querySelector('.cx-parse-btn').onclick = async () => {
                UI.showLoading('正在解析题目...');
                
                try {
                    currentData = await CXParser.parseAll();
                    
                    if (currentData.length) {
                        PreviewUI.show(currentData);
                        
                        if (CONFIG.CLOUD_API) {
                            try {
                                await DataExporter.uploadToCloud(currentData);
                            } catch (error) {
                                console.error('上传数据失败:', error);
                            }
                        }
                    } else {
                        this.showError();
                    }
                } catch (error) {
                    console.error('解析失败:', error);
                    UI.showNotification('解析过程中发生错误: ' + error.message, 'error');
                }
                
                UI.hideLoading();
            };
            
            document.body.appendChild(toolbar);

            const style = document.createElement('style');
            style.textContent = `
                #cx-toolbar {
                    position: fixed;
                    top: 40px;
                    right: 10px;
                    background: white;
                    padding: 6px;
                    border-radius: 8px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
                    z-index: 10000;
                    transition: transform 0.3s ease;
                    user-select: none;
                }
                
                #cx-toolbar.hidden { transform: translateX(calc(100% + 30px)); }
                
                .cx-parse-btn {
                    padding: 10px 20px;
                    background: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    transition: all 0.2s;
                }
                
                .cx-parse-btn:hover {
                    background: #1976D2;
                    transform: translateY(-2px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                
                @media (max-width: 480px) {
                    #cx-toolbar { top: 10px; right: 10px; }
                }
            `;
            document.head.appendChild(style);
            
            // 恢复上次保存的位置
            const savedPos = localStorage.getItem('CX_TOOLBAR_POS');
            if (savedPos) {
                try {
                    const { left, top } = JSON.parse(savedPos);
                    toolbar.style.left = left;
                    toolbar.style.top = top;
                    toolbar.style.right = 'auto';
                } catch (e) {
                    console.error('恢复工具栏位置失败', e);
                }
            }
        }
        
        static makeToolbarDraggable(toolbar) {
            let isDragging = false;
            let offsetX, offsetY;
            
            toolbar.addEventListener('mousedown', (e) => {
                isDragging = true;
                const rect = toolbar.getBoundingClientRect();
                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;
                
                // 添加动画过渡禁用，避免拖拽时有延迟感
                toolbar.style.transition = 'none';
                
                // 添加拖拽时的视觉效果
                toolbar.style.opacity = '0.8';
                
                e.preventDefault();
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                
                const x = e.clientX - offsetX;
                const y = e.clientY - offsetY;
                
                // 确保不会被拖出视口
                const maxX = window.innerWidth - toolbar.offsetWidth;
                const maxY = window.innerHeight - toolbar.offsetHeight;
                
                toolbar.style.left = Math.max(0, Math.min(x, maxX)) + 'px';
                toolbar.style.top = Math.max(0, Math.min(y, maxY)) + 'px';
                toolbar.style.right = 'auto';
            });
            
            document.addEventListener('mouseup', () => {
                if (!isDragging) return;
                isDragging = false;
                
                // 恢复动画过渡
                toolbar.style.transition = '';
                
                // 恢复透明度
                toolbar.style.opacity = '';
                
                // 保存位置到本地存储
                localStorage.setItem('CX_TOOLBAR_POS', JSON.stringify({
                    left: toolbar.style.left,
                    top: toolbar.style.top
                }));
            });
        }

        static initHotkeys() {
            document.addEventListener('keydown', e => {
                if (e.key === CONFIG.HOTKEYS.SHOW) {
                    document.getElementById('cx-toolbar')?.classList.remove('hidden');
                } else if (e.key === CONFIG.HOTKEYS.HIDE) {
                    document.getElementById('cx-toolbar')?.classList.add('hidden');
                }
            });
        }

        static async autoParseAndUpload() {
            if (!CONFIG.CLOUD_API) return;
            
            setTimeout(async () => {
                try {
                    const parsedData = await CXParser.parseAll();
                    if (parsedData.length > 0) {
                        await DataExporter.uploadToCloud(parsedData);
                    }
                } catch (error) {
                    console.error('自动解析上传失败:', error);
                }
            }, CONFIG.DELAY_INIT);
        }
        
        static bindFeedbackEvents() {
            // 使用事件委托处理反馈按钮点击事件
            document.body.addEventListener('click', (e) => {
                const feedbackBtn = e.target.closest('.cx-feedback-btn');
                if (feedbackBtn) {
                    const index = parseInt(feedbackBtn.dataset.index);
                    if (!isNaN(index) && currentData[index]) {
                        UI.createFeedbackUI(currentData[index]);
                    }
                }
            });
        }
        
        static showError() {
            if (parserErrors.length > 0) {
                UI.showNotification(`解析失败: 发现${parserErrors.length}个错误`, 'error');
                UI.showErrorDetails();
            } else {
                UI.showNotification('未找到可解析的题目', 'error');
            }
        }
    }

    // ================= 菜单配置模块 =================
    class MenuManager {
        static init() {
            this.registerMenuCommands();
            this.loadStoredSettings();
        }
        
        static registerMenuCommands() {
            GM_registerMenuCommand('设置上传地址', () => {
                const url = prompt('请输入云端API地址:', CONFIG.CLOUD_API);
                if (url !== null) {
                    CONFIG.CLOUD_API = url.trim();
                    localStorage.setItem('CX_CLOUD_API', url.trim());
                    UI.showNotification('已更新上传地址', 'success');
                }
            });
            
            GM_registerMenuCommand('设置API密钥', () => {
                const key = prompt('请输入API密钥:', CONFIG.API_KEY);
                if (key !== null) {
                    CONFIG.API_KEY = key.trim();
                    localStorage.setItem('CX_API_KEY', key.trim());
                    UI.showNotification('已更新API密钥', 'success');
                }
            });
            
            GM_registerMenuCommand('查看当前设置', () => {
                alert(`
                    当前配置信息:
                    
                    上传地址: ${CONFIG.CLOUD_API || '未设置'}
                    API密钥: ${CONFIG.API_KEY ? '已设置' : '未设置'}
                    收集错题: ${CONFIG.COLLECT_WRONG_ANSWERS ? '开启' : '关闭'}
                `);
            });
            
            GM_registerMenuCommand('开关收集错题功能', () => {
                CONFIG.COLLECT_WRONG_ANSWERS = !CONFIG.COLLECT_WRONG_ANSWERS;
                localStorage.setItem('CX_COLLECT_WRONG_ANSWERS', CONFIG.COLLECT_WRONG_ANSWERS ? '1' : '0');
                UI.showNotification(`已${CONFIG.COLLECT_WRONG_ANSWERS ? '开启' : '关闭'}错题收集功能`, 'success');
            });
            
            GM_registerMenuCommand('重置所有设置', () => {
                if (confirm('确定要重置所有设置吗？这将清除所有保存的配置数据。')) {
                    localStorage.removeItem('CX_CLOUD_API');
                    localStorage.removeItem('CX_API_KEY');
                    localStorage.removeItem('CX_COLLECT_WRONG_ANSWERS');
                    localStorage.removeItem('CX_PREVIEW_POS');
                    localStorage.removeItem('CX_PREVIEW_MINIMIZED');
                    localStorage.removeItem('CX_TOOLBAR_POS');
                    
                    // 重置配置
                    CONFIG.CLOUD_API = '';
                    CONFIG.API_KEY = '';
                    CONFIG.COLLECT_WRONG_ANSWERS = false;
                    
                    UI.showNotification('已重置所有设置', 'success');
                    
                    // 刷新页面以应用更改
                    setTimeout(() => location.reload(), 1000);
                }
            });
        }
        
        static loadStoredSettings() {
            // 从本地存储加载设置
            const storedApi = localStorage.getItem('CX_CLOUD_API');
            const storedKey = localStorage.getItem('CX_API_KEY');
            const storedWrong = localStorage.getItem('CX_COLLECT_WRONG_ANSWERS');
            
            if (storedApi) CONFIG.CLOUD_API = storedApi;
            if (storedKey) CONFIG.API_KEY = storedKey;
            if (storedWrong) CONFIG.COLLECT_WRONG_ANSWERS = storedWrong === '1';
        }
    }

    // ================= 初始化 =================
    setTimeout(() => {
        MenuManager.init();
        MainController.init();
    }, CONFIG.DELAY_INIT);
})();


// 当前脚本来自于http://script.345yun.cn脚本库下载！