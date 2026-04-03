package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug024 {
    public void checkFlag(boolean[] flags, int index) {
        boolean result = false;
        if (result = flags[index]) {
            System.out.println("Flag is set");
        }
    }
}
