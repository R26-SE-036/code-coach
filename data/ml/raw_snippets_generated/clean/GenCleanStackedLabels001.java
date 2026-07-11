public class GenCleanStackedLabels001 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "draft";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
