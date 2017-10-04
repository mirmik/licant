#include <stdio.h>

int main() {

	auto int access ();
	int access () {
		printf("%s\n", "NestedFunction");
    }

    access();

}