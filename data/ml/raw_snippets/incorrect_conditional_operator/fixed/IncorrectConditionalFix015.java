package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix015 {
    public String classify(int score) {
        boolean pass = score >= 50;
        return pass ? "Pass" : "Fail";
    }
}
