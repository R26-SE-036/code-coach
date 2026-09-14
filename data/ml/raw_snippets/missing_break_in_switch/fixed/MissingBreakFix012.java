package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix012 {
    static int permissionLevel(String role) {
        int level = 0;
        switch (role) {
            case "admin":
                level = 3;
                break;
            case "editor":
                level = 2;
                break;
            case "viewer":
                level = 1;
                break;
        }
        return level;
    }
}
