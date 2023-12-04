---
layout: post
title: "Visible Gains and Invisible Losses"
date: 2022-03-03
---



*(This post is pretty long and gets kind of technical. I'm not sure which bits are or aren't clear. So if
 something doesn't make sense or drags a bit, please [email
 me](mailto:raymondadouglas@gmail.com).)*


The harder you try to optimise something, the more likely it is that you will introduce hard-to-detect errors. To
 establish this, we need to assume firstly that there's only so many kinds of changes you can make to your thing,
 and secondly that you can only approximate how good it is. Crucially, we don't have to assume that there are any
 limits on your resources, just limits on the space of your options.


What I'm going to do is provide a mathematical model for optimisation and approximation, and show how it can be
 used to describe Chesterton's Fence and a certain form of Goodhart's Law, as well as a variation on Berkson's
 Paradox.


The model I'm using here is a reduced version that just has one variable: there is a richer model which tracks
 several variables but is much fiddlier, which I am omitting for now. It also draws heavily on Scott Garabrant's
 work on [Goodhart Taxonomy](https://www.lesswrong.com/posts/EbFABnst8LsidYs5Y/goodhart-taxonomy).
 If you're already familiar with that, skip down to "Now with more approximations", which is where the novel
 bits come in.


Toy Example Of Optimisation Being Hard
--------------------------------------


You are a budding Research Manager tasked with setting up a new research group on optimisation theory. There are
 already many of these dotted around the world, but you're determined to make a name for yourself by making an
 even better one.


Your first brilliant insight is that it's easier to improve things if you know what's going on. You notice that
 it would be possible to have your researchers send in reports on their progress far more often. Other programmes
 are not doing this.


You consider that this might reduce the amount of time that they have for research, so you apply for extra
 funding to pay for their food, laundry, and cleaning, offsetting the costs to make it overall good.


Your funders are enthusiastic about this, and sure enough, people send you regular reports and produce far more
 short-term output. Your programme is duly scaled up.


However, you fail to notice that the incentive to produce short-term outputs has in fact nudged your researchers
 towards less exploratory projects, and while they did produce many small discoveries they missed out on a small
 number of far more important but far more out-there discoveries. Worse-funded research groups also fail to do
 this, and nobody ever finds out what was possible.


The Basic Model
---------------


You're trying to do a thing (*run a research group, become friends with someone, eat the right things,
 whatever*). 


You have some number of changes {c1, c2...cn} that you can make to how you do it
 (*get people to send in progress reports, talk to the person about how they're doing, eat a carrot*).


And you have some true score T for 'how well you do it' (*how well is the research group going, is this person
 your friend, are you eating the right things*) which you're trying to maximise, but you don't actually
 know T. But most changes will affect it somehow. Specifically, introducing the change ci will
 increase T by T(ci)[1].


What you do know is the approximation score A (*how well does the research group seem to be going, do you
 think this person is your friend, do you feel like you're eating the right things*). And the changes
 will affect this too, but in a different way. Specifically, introducing the change ci will increase A
 by A(ci).


Depending on your approximation, some changes will improve both A and T, some will improve A without changing T,
 and some will improve A while making T worse. For a change ci we'll say something like
 A(ci)>T(ci)>0 to mean "implementing ci does improve your true score, but
 not as much as you think". 


Taking the food example, if your approximation is "how good does it feel to eat this", then you improve both A
 and T by eating a carrot when you're starving, but eating an entire cake when you're kind of hungry will
 probably increase A and lower T, because it feels good to eat it but it's not particularly healthy. 


The Basic Problem
-----------------


### Goodhart's Law


The simplest example from which all others spring is this: Suppose you want to maximise T, but your only way of
 telling how well you're doing is maximising A. And suppose that there is some ci such that
 A(ci)>0>T(ci). You will, in pursuit of maximising A, implement this change, and make
 things worse.


Now With More Agents
--------------------


#### #1 - The Fence


There are a bunch of people (a1, a2...ah-1) doing a thing. They're all trying to
 get a high true score T, but they all have slightly different ways A1,
 A2...Ah-1 of approximating it, and they've all picked slightly different sets of changes
 C1, C2...Ch-1 to implement, where Ci represents a subset of all
 possible changes {c1, c2...cn}. 


So agent a2 thinks its score is about A2(C2), and it thinks a3's
 score is A2(C3). In reality their scores are T(C2) and T(C3),
 respectively.


And now you appear, a fresh new agent ah. You start by implementing a bunch of changes Ch
 to push Ah up as high as you can. But you notice that there's a change cj which increases
 Ah a lot, but which none of the other agents have implemented.


One possibility is that all of their approximations are wrong, and they're missing the fact that cj is
 a great way of improving T. The other is that only you are wrong. What you have encountered is Chesterton's
 Fence


The real world solution to this is to work out *why* they all think it's bad, such that you either also
 recognise it's bad, or figure out what they're missing about why it's great.


I note that this problem gets immediately far worse if the goal is not 'maximise T' but rather 'get a higher T
 than everyone else'.


### #2: Goodhart's Law, Principal Agent Variant


Suppose you, the mighty a1, send off a2 to do something for you. You roughly reveal your
 approximation function A1 to them, and ask them to work out what the set of changes C1
 that you make should be.


Assuming all they're trying to do is satisfy your approximation function, if there is any ci where
 A1(ci)>0, they will include it, even if 0>T(ci). Note that even if
 0>A2(ci), it's still in their interest to do it if they're just trying to please you.
 


(This is a very rough summary of why outer alignment of artificial intelligence is hard.)


### #3: Goodhart's Law, Multi-Agent Variant


Suppose you are the boss a1, and you send a bunch of other agents a2...ah out
 into the world to find the best way of doing the thing. And after some optimisation time, they all come back to
 you with their attempts to maximise the true score.


Suppose A1(ci)>0>T(ci) - you think the change ci helps even
 though it actually makes things worse. And suppose that in fact most of your agents aj have correctly
 determined that Aj(ci)<0, except for one, am, where
 Am(ci)>0. If agent am differs from agent ak only in whether or
 not it implements change cj, then am will outperform ak in your estimation
 despite being worse.


The more of them there are, and the worse your ability to approximate how well they're doing, the more likely it
 is that the one which looks the best is approximating badly in the same way as you. This also gets way worse if
 you somehow reward the 'best' and encourage others to emulate them.


(This is why community building and funding is hard, and also inner alignment.)


Now With More Approximations
----------------------------


We can extend this notion of approximations further by supposing that you have several to compare with each
 other, and this is where really weird effects start to emerge.


### #4: Berkson's Paradox, Further Change Variant


Let's suppose you have two approximations, P and Q, neither of which quite captures the true value T. To begin
 with, you'll pick up loads of value by making all the changes both P and Q recommend, and ignoring the ones they
 both recommend against. 


But there's a third category, which is changes that improve one approximation and lower the other. The crucial
 insight here is that if any of these things exist, then you will quickly reach a stage where you've run out of
 obvious improvements, and in fact from then on, for any remaining ci, you will find P(ci)
 and Q(ci) are anticorrelated. This is even stronger if you fully ignore things which make everything
 worse. So further optimisation of either proxy will necessarily come at the expense of the other.


(For example, you can treat P as 'what I think is right' and Q as 'what everyone else thinks is right'. Once
 you've done everything you want which everyone else supports, you'll be left with things where the more you want
 them, the more everyone else seems to disapprove, in general.)


You might be lucky enough to find pairs of changes ci and cj such that
 P(ci)<0 and Q(cj)<0, but P(ci+cj), Q
 (ci+cj) > 0, ie there are individual changes which both recommend against, but both
 recommend that you adopt a combination of the two.


The phenomenon here looks a bit like Berkson's Paradox, which states that if you have a bunch of points (eg
 people) with two uncorrelated variables sampled from two distributions (eg competence and kindness, as a proxy
 for 'how good an employee are they'), and then you cut out everything below a certain threshold on both (eg an
 organisation that fires people who are both incompetent and unkind), then in the remaining pool those variables
 will become anticorrelated (ie on average, the kinder someone is, the less competent you should expect them to
 be).


But it actually shows something slightly different, because it's sensitive to change among points in a different
 way. Berkson's Paradox is based on a threshold, and the anticorrelation is sustained by the fact that people are
 either above or below that threshold, but beyond that the anticorrelation vanishes for individuals. So going
 back to the organisation example, Berkson's Paradox does not imply that as someone becomes more competent, they
 also become less kind.


My model unfortunately does imply this under certain assumptions. Suppose you take a specific person who makes
 choices under a policy that seeks to maximise either competence or kindness. They will find that the further
 they optimise, the more likely it is that the policy changes which increase one variable will require them to
 sacrifice the other one.


Footnotes
---------


[1] - Why make it linear? It very much isn't, but we're usually going to be comparing two agents that differ by
 one or two changes, and even if the function isn't globally linear it will be locally.


Related Things
--------------


[Limits to Legibility](https://www.lesswrong.com/posts/4gDbqL3Tods8kHDqs/limits-to-legibility)  

[What failure looks like](https://www.lesswrong.com/posts/HBxe6wdjxK239zajf/more-realistic-tales-of-doom)

