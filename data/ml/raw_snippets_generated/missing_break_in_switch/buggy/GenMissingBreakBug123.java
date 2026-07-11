public class GenMissingBreakBug123 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "shipped";
            case 3:
                label = "final";
                break;
            case 4:
                label = "closed";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }
}
