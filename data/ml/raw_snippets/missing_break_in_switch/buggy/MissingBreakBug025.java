package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug025 {
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
            case 'F':
                comment = "Failed";
                break;
        }
        System.out.println(comment);
    }
}
