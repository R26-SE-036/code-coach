package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix024 {
    public void checkFlag(boolean[] flags, int index) {
        boolean result = flags[index];
        if (result) {
            System.out.println("Flag is set");
        }
    }
}
