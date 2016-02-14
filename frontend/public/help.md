# CPPR: <br />Collaborative(ly) Personalized PageRank User Study

## TL; DR

- This user study is for you to select "top 5 most relevant" (per column/ranking list) results, __in accordance to a
given context__ among two presented rankings and also __which ranking is the best, overall__ (left/right).

- You can select between 0 and 5 results (**per column**!). You do not necessarily need to select 5. If you want to
select more than 5, keep the best (in your opinion) 5 ones.

- __There are only 5 queries, so do not hesitate to click on links (blue titles / green urls) and make sure about what you
think is best.__

- __A "Help" button will be on the left__, to bring back this modal window in case you need.

- __Left/Right rankings are randomly swapped__ at every page reload, so that you cannot be biased by a left/right
preference. Do not make assumptions about wheter the left or right side is better, it is going to change.

- __This is not Google__: Results might seem a little bit "crap" sometimes in comparison with Google. Those queries were
matched against a focused/small crawl of the WWW and this is not Google, the results are as good as the web repository
can be.

## TL; DR; Pictures! (Visual Tutorial)

In a nutshell, here's the GUI and what you have to do on it:
![][visututo]

[visututo]: ./images/tutorial.png width=800 height=724


<a style='display:block;text-align:center; font-size: 2em;' href='#top' onclick='$.colorbox.close();'>
&gt;&gt; ENOUGH READING, LET'S GO! &lt;&lt;
</a>


## Normal Version

Welcome to the CPPR User Study.

The goal of this study is to provide a user-based relevance measurement to 
a pre-selected set of rankings.

Based on the results of the user study, I will be able to make conclusion on
the performance of the algorithm that I have been developing during my Master 
Thesis: Collaborative(ly) Personalized PageRank.

## How The User Study Works

During the user study, every "user" will be presented with the same sequence
of rankings. These rankings have a _context_. This context is basically clicks/navigation
of users similar to the "current user" (similar = similar user profile). These are used
in an attempt to re-rank the SERP (Search Engine Result Page) results to be more tailored
to the "current user" profile, using information from similar users.

__Your mission, if you accept it, is to imagine you are this user__, the context is often quite
short: Only a couple of links are taken into account (due to several layers of intersections),
simply try to imagine, if you had clicked on such links, what would you be looking for.

Based on this, you can then __select at most 5 results (per column!)__ that are _relevant_. There can be less
than 5, but not more than 5 (the UI won't allow more than 5 selected results).

If you really think none of the results are relevant, you can select none of them, a confirmation
will however be asked, to be sure you did not just forget to select them.

Amongst those two rankings, one of them is using the "standard" PageRank algorithm.
The other one has been computed using personalized weights extracted based on the context
of users similars to him/her.

You will not know which ranking is personalized or not (although you might guess).
__And the rankings will randomly be swapped sides for every query that you see__. So, please
__do not make any assumptions on whether one side is better than the other one__ because they
_are randomly swapped_.

## What Is A _Relevancy Judgment_

A relevancy judgment is just: You consider that this result (a link/snippet) is
relevant to the query that is being presented and with the current context (the context is important).

## How Do You Provide Your Judgments?

You simply have to left-click a result to mark it as relevant. It will turn green.
If you misclicked, simply click again on the same result to toggle its relevant/irrelevant state.

__You can select between 0 and 5 relevant results__ (per column!). If more than 5 results are relevant in your opinion,
select the 5 most relevant ones for left/right columns. If less than 5 results are relevant in your opinion, just select
the ones you think are relevant and validate as is.

## Global Opinion On Best Ranking "Overall"

The last thing that will be asked to you is to provide, for every query/context, your overall
preference towards one ranking or the other.

__This time, you have to choose, you cannot select both__. Simply select the one
that in your opinion globally answers the best the query / context. Rankings should never
be exactly similar so you should not have to make non-sense choices.


<a style='display:block;text-align:center; font-size: 3em;' href='#top' onclick='$.colorbox.close();'>
OK LET'S GO!
</a>

## Want To Know More About Cppr?

This help page is a little bit too short to explain in details. If you feel you need more details to do the user query,
then please contact me (see at the bottom) but that should not be needed.

## Want To Know Even More About Cppr?

Just shoot me <a id="shoot_an_email" href="mailto:__myemail__">an email</a> and I will be happy sending my Master
Thesis to you in its current state or when it's finalized :) Be warned: That's quite a bunch 
of pages.

<script type="text/javascript">
var a = "theod"
var b = ".insa"
var c = "@"
var mto = ["m", "a", "i", "l", "t", "o", ":"]
document.getElementById("shoot_an_email").href = mto.join("") + a + b + [c, "gm", "ail"].join("") + ("." + "com")
</script>