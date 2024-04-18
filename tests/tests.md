# Tests list

_Ignoring fields `400` & `410`_

* Record `001  000000001` : no error & nothing happening
* Record n°2 :
  * No `001` or `035` : error `NO_RECORD_ID`
* Record n°3 :
  * No `001`,  `035` without `$a` : error `NO_RECORD_ID`
* Record `035 $a(OCoLC)0000000010` : no error on the ID retrieval
* Record `001  000000100` :
  * `400` & `410` : nothing happening, fields are ignored
* Record `001  000000101` :
  * `411` with no `$x`, `$y` & not matching the manual check sample : nothing happening
  * `412` with `$t` matching exactly the manual check for `123456` : `412` is changed to `$0123456$tCréateurs du Japon$aLabbé, Françoise (19..-....)$p1 vol. (199 p.)$y2-7056-6058-5`
  * `413` with `$t` matching the manual check for `123456` if normalised : `413` is changed to `$0123456$tCréateurs du Japon$aLabbé, Françoise (19..-....)$p1 vol. (199 p.)$y2-7056-6058-5`
  * `414` with `$t` matching exactly the manual check for `123457` : `414` is changed to `$0123457$tLe patrimoine mondial$aAudrerie, Dominique (1953-....)$p1 vol. (127 p.)$v3436$y2-13-049646-6`
  * `415` with `$t` matching the manual check for `123457` if noramlised : nothing happening
  * `416` with `$t` matching exactly the manual check for `123457` & a `$y` matching biblionumber `538789` & a `$x` matching biblionumber `162` : `416` is changed to `$0123457$tLe patrimoine mondial$aAudrerie, Dominique (1953-....)$p1 vol. (127 p.)$v3436$y2-13-049646-6`
  * `417` with `$t` matching exactly the manual check for `123458` but no `$a` : nothing happening
  * `418` with `$t` & `$a` matching exactly the manual check for `123458` : `418` with `$0123458$tLes jardins du futur$aPigeat, Jean-Paul (1946-2005)$cChaumont-sur-Loire$d2000$nConservatoire International des Parcs et Jardins et du Paysage$o9e festival international des jardins de Chaumont-sur-Loire$p175 p.`
  * `419` with nothing matching manual checks, a `$y` matching biblionumber `538789` & a `$x` matching biblionumber `162` : `419` with `$0162$tCriticat$cParis$d2008-2018$nAssociation Criticat$x1961-5981`
  * `420` with nothing matching manual checks, a `$y` matching biblionumber `538789` : `420` with `$0538789$tL'hôpital Beaujon de Clichy$aBonneau, Lila (1990-....)$ol'architecture thérapeutique du XXe siècle et ses milieux$p1 volume (204 pages)$y979-10-370-2967-6`
  * `421` with a `$y` matching biblionumber `538789` if normalised : `421` with `$0538789$tL'hôpital Beaujon de Clichy$aBonneau, Lila (1990-....)$ol'architecture thérapeutique du XXe siècle et ses milieux$p1 volume (204 pages)$y979-10-370-2967-6`
  * `422` with a `$x` matching biblionumber `162` if normalised : `422` with `$0162$tCriticat$cParis$d2008-2018$nAssociation Criticat$x1961-5981`
  * `423` with a `$y` matching biblionumber `117079` : `423` with `$0117079` & `$e[Nouv. éd. révisée]` and no `$y` (erroneous ISBN is in the record in the first `010` which has no `$a`)
  * `424` with a `$y` matching biblionumber `116686` : `424` with `$0116686`, `$h11`, `$i[index général]`
  * `425` with a `$y` matching biblionumber `22636` : `425` with `$022636` & `$h1997-2`
  * `426` with a `$y` matching biblionumber `387687` : `426` with `$0387687` & `$hLibro 1-5`
  * `427` with a `$y` matching biblionumber `117757` : `427` with a `$0117757` & `$iGéographie`
  * `428` with a `$y` matching iblionumber `372603` : `428` with a `$0372603` & `$iA.T.`
  * `429` with a `$y` matching biblionumber `545143` : `429` with a `$0545143` & `$l= Home of the future`
  * `430` with a `$x` matching biblionumber `187` : `430` wiht a `$0152259` & no `$x`
  * _`200$a` is mandatory so we're not testing `$t`_
  * _Authors things are a pain to check & seems to work so no testing the full behaviour_