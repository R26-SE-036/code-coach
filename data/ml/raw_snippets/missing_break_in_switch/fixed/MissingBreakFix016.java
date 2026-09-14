package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix016 {
    public static void main(String[] args) {
        int x = 0;
        int y = 0;
        char command = 'N';
        switch (command) {
            case 'N':
                y++;
                break;
            case 'S':
                y--;
                break;
            case 'E':
                x++;
                break;
            case 'W':
                x--;
                break;
        }
        System.out.println(x + "," + y);
    }
}
