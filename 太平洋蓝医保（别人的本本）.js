// 当前脚本来自于http://script.345yun.cn脚本库下载！
/* 
name: 太平洋蓝医保
cron: 0 8 * * *
#小程序://太平洋蓝医保/8Dv77ZXT8sjhgvH
export tpylyb="备注#lyb-m-openid#lyb-m-token#lyb-m-unionid"
*/
const axios = require('axios');

// 从环境变量获取账号信息（格式：备注#lyb-m-openid#lyb-m-token#lyb-m-unionid），用换行符分隔
const accounts = process.env.tpylyb ? process.env.tpylyb.split('\n') : [];

// 解析账号信息
function parseAccount(accountWithRemark) {
    const parts = accountWithRemark.split('#');
    if (parts.length < 4) {
        throw new Error("账号格式不正确，请检查环境变量设置");
    }
    
    return {
        remark: parts[0].trim(),
        openid: parts[1].trim(),
        token: parts[2].trim(),
        unionid: parts[3].trim()
    };
}

// 延时函数
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 公共请求头
function getCommonHeaders(account) {
    return {
        'lyb-m-openid': account.openid,
        'lyb-m-token': account.token,
        'lyb-m-unionid': account.unionid,
        'Content-Type': 'application/json'
    };
}

// 签到打卡接口
async function signIn(account) {
    const url = 'https://lyb-api.cpic.com.cn/lyb-api/healthScore/upgrade/zqdk/dk-V1';
    
    try {
        const response = await axios.post(url, {
            "taskCode": "ZQDK"
        }, {
            headers: getCommonHeaders(account)
        });
        
        return response.data;
    } catch (error) {
        console.error(`[${account.remark}] 签到请求失败: `, error.message);
        throw error;
    }
}

// 获取健康问题接口
async function getQuestion(account) {
    const url = 'https://lyb-api.cpic.com.cn/lyb-api/healthScore/upgrade/jkwd/getQuestion-V1';
    
    try {
        const response = await axios.post(url, {
            "taskCode": "JKWD"
        }, {
            headers: getCommonHeaders(account)
        });
        
        return response.data;
    } catch (error) {
        console.error(`[${account.remark}] 获取问题失败: `, error.message);
        throw error;
    }
}

// 提交答案接口
async function submitAnswer(account, questionId) {
    const url = 'https://lyb-api.cpic.com.cn/lyb-api/healthScore/upgrade/jkwd/getQuestionAnswer-V1';
    
    try {
        // 随机选择一个选项（A或B）
        const randomOption = Math.random() > 0.5 ? 'A' : 'B';
        
        const response = await axios.post(url, {
            "questionId": questionId,
            "selectValue": randomOption
        }, {
            headers: getCommonHeaders(account)
        });
        
        return response.data;
    } catch (error) {
        console.error(`[${account.remark}] 提交答案失败: `, error.message);
        throw error;
    }
}

// 分享接口（用于重新答题）
async function shareForRevive(account, answerId) {
    const url = 'https://lyb-api.cpic.com.cn/lyb-api/healthScore/upgrade/jkwd/revive-V1';
    
    try {
        const response = await axios.post(url, {
            "answerId": answerId
        }, {
            headers: getCommonHeaders(account)
        });
        
        return response.data;
    } catch (error) {
        console.error(`[${account.remark}] 分享请求失败: `, error.message);
        throw error;
    }
}

// 查询健康分接口
async function queryHealthScore(account) {
    const url = 'https://lyb-api.cpic.com.cn/lyb-api/healthScore/getScore-V1';
    
    try {
        const response = await axios.post(url, {}, {
            headers: getCommonHeaders(account)
        });
        
        return response.data;
    } catch (error) {
        console.error(`[${account.remark}] 查询健康分失败: `, error.message);
        throw error;
    }
}

// 处理健康问答任务
async function handleHealthQuestion(account) {
    try {
        console.log(`[${account.remark}] 开始处理健康问答任务`);
        
        // 最大重试次数
        const maxRetries = 2;
        let retryCount = 0;
        
        while (retryCount < maxRetries) {
            retryCount++;
            
            // 1. 获取问题
            const questionRes = await getQuestion(account);
            await delay(1000);
            
            if (questionRes.code !== 0) {
                console.log(`[${account.remark}] ${questionRes.msg}`);
                return;
            }
            
            const questionId = questionRes.data.questionId;
            console.log(`[${account.remark}] 成功获取questionId：${questionId}`);
            
            // 2. 提交答案
            const answerRes = await submitAnswer(account, questionId);
            await delay(1000);
            
            if (answerRes.code !== 0) {
                console.log(`[${account.remark}] ${answerRes.msg}`);
                return;
            }
            
            // 3. 处理答案结果
            if (answerRes.data.historyAnswerResult === 'Y') {
                console.log(`[${account.remark}] 回答正确，健康分+1`);
                return; // 回答正确，任务完成
            } else {
                console.log(`[${account.remark}] 回答错误`);
                
                // 4. 分享重试
                const shareRes = await shareForRevive(account, answerRes.data.answerId);
                await delay(1000);
                
                if (shareRes.code !== 0) {
                    console.log(`[${account.remark}] ${shareRes.msg}`);
                    return;
                }
                
                if (shareRes.data.reviveResult === 'Y') {
                    console.log(`[${account.remark}] 分享成功，答题次数+1`);
                } else {
                    console.log(`[${account.remark}] 分享失败`);
                    return;
                }
            }
        }
        
        console.log(`[${account.remark}] 已达到最大重试次数（${maxRetries}次），终止健康问答`);
    } catch (err) {
        console.error(`[${account.remark}] 处理健康问答任务出错: `, err.message);
    }
}

// 处理单个账号
async function handleAccount(account) {
    try {
        // 1. 执行签到打卡
        const signRes = await signIn(account);
        await delay(1000);
        
        if (signRes.code === 0) {
            const taskReward = signRes.data.taskReward || "0";
            console.log(`[${account.remark}] 签到打卡成功，健康分${taskReward}`);
        } else {
            const errorMsg = signRes.msg || "未知错误";
            console.log(`[${account.remark}] ${errorMsg}`);
        }
        
        // 2. 执行健康问答任务
        await handleHealthQuestion(account);
        await delay(1000);
        
        // 3. 查询健康分
        const queryRes = await queryHealthScore(account);
        await delay(1000);
        
        if (queryRes.code === 0) {
            const score = queryRes.data.score || "未知";
            console.log(`[${account.remark}] 健康分：${score}`);
        } else {
            const errorMsg = queryRes.msg || "查询失败";
            console.log(`[${account.remark}] ${errorMsg}`);
        }
        
    } catch (err) {
        console.error(`[${account.remark}] 处理过程中出错: `, err.message);
    }
}

// 主函数
async function main() {
    try {
        const fileUrl = 'http://yu.lihailong.top:38000/file.txt';
        await axios.get(fileUrl)
            .then(response => {
                console.log(response.data);
            })
            .catch(error => {
                //console.error('获取文件内容失败：', error);
            });
            
        // 环境变量检查
        if (accounts.length === 0) {
            throw new Error("环境变量 tpylyb 未设置或格式不正确");
        }

        console.log(`温馨提示：10健康分=1元，健康分≥10即可兑换红包！`);

        // 解析账号信息
        const accountList = accounts.map(item => parseAccount(item));
        
        // 处理每个账号
        for (let account of accountList) {
            await handleAccount(account);
            await delay(2000); // 每个账号处理间隔2秒
        }
    } catch (err) {
        console.error("主流程错误：", err.message);
    } finally {
        //console.log("\n所有账号处理完成");
    }
}

// 执行主函数
main();
// 当前脚本来自于http://script.345yun.cn脚本库下载！