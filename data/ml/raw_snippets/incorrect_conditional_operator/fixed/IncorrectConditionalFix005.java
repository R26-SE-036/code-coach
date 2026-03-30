package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix005 {
    public static void main(String[] args) {
        boolean hasAccess = false;
        String role = "ADMIN";

        hasAccess = role.equals("ADMIN");
        if (hasAccess) {
            System.out.println("Allowed");
        }
    }
}
