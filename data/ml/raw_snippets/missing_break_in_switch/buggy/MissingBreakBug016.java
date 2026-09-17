package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug016 {
    public static void main(String[] args) {
        int x = 0;
        int y = 0;
        char command = 'N';
        switch (command) {
            case 'N':
                y++;
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
