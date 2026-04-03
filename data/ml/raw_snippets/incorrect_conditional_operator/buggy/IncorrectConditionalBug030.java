package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug030 {
    public void checkMatch(String a, String b) {
        boolean matched = false;
        if (matched = a.equalsIgnoreCase(b)) {
            System.out.println("Strings match");
        }
    }
}
