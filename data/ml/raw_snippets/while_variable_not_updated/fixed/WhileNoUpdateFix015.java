package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix015 {
    static String padLeft(String text, int width) {
        String padded = text;
        while (padded.length() < width) {
            System.out.println("padding...");
            padded = " " + padded;
        }
        return padded;
    }
}
