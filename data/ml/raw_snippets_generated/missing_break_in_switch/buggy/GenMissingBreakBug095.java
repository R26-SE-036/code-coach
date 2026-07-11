public class GenMissingBreakBug095 {
    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
            case 2:
                label = "paid";
                break;
            case 3:
                label = "queued";
                break;
            case 4:
                label = "final";
                break;
            case 5:
                label = "draft";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
