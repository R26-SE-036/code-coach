public class GenCleanStackedLabels007 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "new";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static boolean isEven1(int total) {
        return total % 2 == 0;
    }
}
