HTML header:    <script type="text/javascript"
                src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
                </script>

<style type="text/css">
.done, span.done, span.done ins {
    color: green !important;
}
.added::before, ins::before {
    content: " ++ ";
    /*font-size: 0.8em;*/
    font-weight: bold;
}
.added, ins {
    color: blue;
    text-decoration: none;
}
del {
    color: red;
}

.past {
    opacity: 0.7;
    display: block;
}
.past:hover {
    opacity: 1.0;
}

.current {
    font-size: 1.6em;
    color:red
;}
</style>
<meta charset="UTF-8">

## Legend

- <span class='done'>Tasks that are finished in green</span>
- __Tasks in progress in bold__
- {++Tasks that have been added to the original schedule in blue (additionnal, unpredicted, tasks, or moved tasks from 
other periods)++}
- *[{--original date--} re_scheduled_date]*

## Schedule

### July

#### <span class="past">14/07 - 24/07</span>

- <span class='done'>User profiles compilation: Formula definition. *[14-15/07 - done]*</span>
- <span class='done'>Adaptation of the formula from "A large scale evaluation of Personalized Search Strategies" to fit our needs and our data.
*[14-16/07 - done]*</span>
- <span class='done'>Use of Lyes Limam's clusters *[15/07 - done]*</span>
- <span class='done'>Comparative study of existing formula. *[16/07 - done]*
- <span class='done'>Parallel light work on the written work *[entire period - more or less done]*</span>
- <span class='done'>{++sim() computation optimization and parallelization++} *{++[17-18, 21-24/07++}* - *done]*</span>
- <span class='done'>Collaborative Personalized PageRank coding *[15/07, 17/07, {++24-25/07++} - done]*</span>
- <span class='done'>Definition of the queries to be used for evaluation/user study *[18-22/07 - done]*</span>
- <span class='done'>First Collaborative Personalized PageRank test runs on small set of data *[{--22--} 24-{--24--} 26/07]*</span>
- <span class='done'>Meeting with Andreas and {--Harald--}(Germany), {--Sylvie--} and Léa (France) *[24/07 - done]*</span>

#### <span class="past">24/07 - 01/08</span>

- <span class='done'>{++Definition of the _users_ to be used for evaluation/user study++} *{++[XX-XX/07]++}* DONE</span>
- <span class='done'>{++Understand why the top-similar users have 1.0 similarity -> have they really same profile? get rid of 
them++} *{++[24-25, 27-28/07]++}* DONE</span>
    + {--{++Either by restricting the users we take into account (threshold on the number of queries, for instance) (might be 
    tricky choosing the right threshold(s))++}--}
    + <span class='done'>__{++Or just discarding users that have similarity = 1.0 from the top user list (might end up with all 0.99...)++} [
    done](3k with 0.99-like scores)__</span>
- <span class='done'>Web UI / User Study UI development *[{--24--}26-{--26--}27/07 - done]* </span>
- <span class='done'>First user test: Seeing if the UI is easy to use/understand with one or two real-world users *[27/07 - 
done]* </span>
- <span class='done'>Necessary changes in the UI *[{--28--}27-29/07 - done]*</span>
- <span class='done'>Pre-processing of the chosen requests data (users, clicks, user queries scores, PageRank vectors...) *[28-31 - 
done]*</span>
- <span class='done'>Parallel light work on the written work** *[entire period - done]*</span>

### August

#### <span class='past'>04/08 - 10/08</span>

- <span class='done'>{++Backend of the web UI: saving clicks, sessions, forward/backward browsing++} {++*[one day]*++}</span>
- <span class='done'>First draft of the written work</span>
    + Related work
        * {--User modeling--} _Moved to last period of August_
        * {--Personalized Search / Recommender systems / collaborative filtering--} _Moved to last period of August_
        * <span class='done'>PageRank & Personalized PageRank</span>
    + <span class='done'>Introduction</span>
    + <span class='done'>Main Contribution</span>
        * <span class='done'>Usage extraction</span>
        * <span class='done'>Personalization score</span>
        * <span class='done'>Graph Scoring</span>
        * <span class='done'>PageRank Personalization</span>
    + <span class='done'>Experimentation</span>
        * <span class='done'>Introduction</span>
        * <span class='done'>Dataset Enrichment</span>
        * <span class='done'>Dataset Enrichment</span>
    + <span class='done'>Evaluation</span>
        * <span class='done'>Dataset</span>
            - <span class='done'>Origin</span>
            - <span class='done'>Content</span>
            - <span class='done'>Statistics</span>
            - <span class='done'>Caracteristics</span>
        * {--Measures--} _Moved to last period of August_
        * {--User study protocol--} _Moved to last period of August_
- <span class='done'>Miscelaneous stuff related to implementation that could be needed... </span>
- {--Development of scripts to extract and analyze results of user study?--} _Moved to last period of August_
- <span class='done'>Needed changes (there will be...) in user study protocol if any</span>

#### <span class='past'>10/08 - 14/08</span>

- <span class='done'>Last review of the user study protocol... </span>
- <span class='done'>User study system deployment on Internet *[10-13/08]*</span>
- <span class='done'>Launch of the user study *[10-13/08]*</span>
- {--Parallel light work on the written work--}

#### <span class='past'>18/08 - 28/08</span>

- <span class='done'>Written work</span>
    + <span class='done'>ElasticSearch *[20/08 - done]*</span>
    + <span class='done'>Finish the "web crawl" section *[20/08 - done]*</span>
    + <span class='done'>Explain the "mapping" Web Graph 2014 $\leftrightarrow$ 2006 *[20/08 - done]*</span>
    + <span class='done'>{++Related work++} _(moved from 4-10/08 period)_</span>
        * <span class='done'>{++User modeling++} *[20-22/08 - done]* _(moved from 4-10/08 period)_</span>
        * <span class='done'>{++Personalized Search / Recommender systems / collaborative filtering++} [21-23/08 - done] _(moved from 4-10/08 period)_</span>
            - <span class='done'>Intro / classification *[21-23/08]*</span>
            - <span class='done'>Content-based *[22-23/08]*</span>
            - <span class='done'>Collaborative & hybrid *[23-25/08 - done]*</span>
    + <span class='done'>{++Evaluation++}</span>
        * <span class='done'>{++Measures++} *[23-24/08]* _(moved from 4-10/08 period)_</span>
        * <span class='done'>{++User study protocol++} *[22/08 - done]* _(moved from 4-10/08 period)_</span>
        * <span class='done'>Queries selection protocol *[23/08 - done]*</span>
    + <span class='done'>Implementation/Experimentation</span>
        * <span class='done'>PageRank Computation</span>
            - <span class='done'>Pre-computation *[ASAP/08]*</span>
                + <span class='done'>CPPR Computation</span>
                + <span class='done'>Final Rankings Generation</span>
            - {--Storage (? remove this ?)--}
            - <span class='done'>Online retrieval (transformed into "rank merging") *[ASAP/08]*</span>
        * {--Online platform development/design choices description?--}
- <span class='done'>{++Development of scripts to extract and analyze results of user study?++} *[23/08]* _(moved from 4-10/08 period)_</span>
    + <span class='done'>Rankings preferences</span>
    + <span class='done'>Rankings precisions</span>
    + <span class='done'>Rankings precisions differences volunteer-wise</span>
    + <span class='done'>{++OSim/KSim++} *[27/08 - done]*</span>
- <span class='done'>INSA 10 pages report *[25-28]* **deadline is the 28/08 23h59**</span>
- <span class='done'>All the rest of the written work...</span>

### September

#### 28/08 - 05/09

- {--Analyze of the first user study results if any--}
- {--Integration in the written work *[iteration 1]*:--}
- {--Continuation of the written work where it is not finished yet *[iteration 1]*--}
    + {--Conclusion--}
    + {--Future Work--}
    + <span class='done'>TODOs fixing manuscript-wide</span>
- <span class='done'>{++Proofreading++}</span>
    + <span class='done'>0-27 [29/08, 01/09]</span>
    + <span class='done'>27-50 [2/9]</span>
    + <span class='done'>50-85 [3/9]</span>
    + <span class='done'>85-100 [4/9]</span>
    + <span class='done'>100-115 [5/9]</span>
- <span class='done'>{++Preparation of the defense presentation (1st part)++} moved from 11-12/09 period</span>

#### 05/09 - 10/09

- <span class='done'>{++Preparation of the defense presentation (continued) ++} moved from 11-12/09 period</span>
- <span class='done'>{++Defense with INSA de Lyon & Passau++} *[10/09]*_moved from 12/9_</span>
- <span class='done'>Analyze of the user study results</span>
- <span class='done'>Integration in the written work *[iteration 2]*</span>
- <span class='done'>Continuation of the written work where it is not finished yet *[iteration 2]*</span>
- {--Hand out of the final version of the written work--} _moved to next period_
- {--In case I get any spare time: work on the defense presentation--}

#### <span class='current' id='current'>11/09 - 12/09</span>

- {--Preparation of the defense presentation--} moved to 28/08-05/09 period

#### 12/09 - 19/09

- {--Defense with INSA de Lyon (French partner university)--} _moved to 10/9_
- {++Integration of the potential comments from the defense into the written work++}
- {++Administrative deposit of the written work @ Passau Universität Prüfungssekretariat++}