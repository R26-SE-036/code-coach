public class GenIncorrectConditionalFix152 {
    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static String report(boolean enabled) {
        if (enabled == true) {
            return "draft";
        }
        return "queued";
    }
}
