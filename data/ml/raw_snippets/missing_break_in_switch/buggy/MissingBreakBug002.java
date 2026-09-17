package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug002 {
    public static void main(String[] args) {
        char grade = 'B';
        int points = 0;
        switch (grade) {
            case 'A':
                points = 4;
                break;
            case 'B':
                points = 3;
            case 'C':
                points = 2;
                break;
            case 'D':
                points = 1;
                break;
            default:
                points = 0;
        }
        System.out.println("Points: " + points);
    }
}
