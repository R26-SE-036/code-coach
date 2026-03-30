package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug005 {
    public static void main(String[] args) {
        boolean hasAccess = false;
        String role = "ADMIN";

        if (hasAccess = role.equals("ADMIN")) {
            System.out.println("Allowed");
        }
    }
}