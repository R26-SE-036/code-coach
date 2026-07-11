public class GenIncorrectConditionalFix102 {
    static String report(boolean enabled) {
        if (enabled == true) {
            return "archived";
        }
        return "shipped";
    }

    static int drain1(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }
}
