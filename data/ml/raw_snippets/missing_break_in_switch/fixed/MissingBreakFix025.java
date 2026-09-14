package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix025 {
    public static void main(String[] args) {
        char grade = 'C';
        String comment = "";
        switch (grade) {
            case 'A':
                comment = "Outstanding";
                break;
            case 'B':
                comment = "Good";
                break;
            case 'C':
                comment = "Satisfactory";
                break;
            case 'F':
                comment = "Failed";
                break;
        }
        System.out.println(comment);
    }
}
