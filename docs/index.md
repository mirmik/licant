---
layout: default
---

#Licant

Licant предназначен для сборки небольших модульных проектов с зависимостями.

Установка
---------
{% highlight sh %}
python3 -m pip install licant
{% endhighlight %}

HelloWorld
----------
{% highlight python %}
#!/usr/bin/env python

import licant.make as lmake
import licant

lmake.source("a.txt")
lmake.copy(tgt = "build/b.txt", src = "a.txt")
lmake.copy(tgt = "build/c.txt", src = "build/b.txt")

print("licant targets list:" + str(licant.core.core.targets))

licant.ex(default = "build/c.txt")
{% endhighlight %}