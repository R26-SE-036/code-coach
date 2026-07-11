public class GenCleanStackedLabels019 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "draft";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
