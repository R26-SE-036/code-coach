public class GenIncorrectConditionalBug053 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static String report(boolean loaded) {
        if (loaded = true) {
            return "archived";
        }
        return "closed";
    }
}
