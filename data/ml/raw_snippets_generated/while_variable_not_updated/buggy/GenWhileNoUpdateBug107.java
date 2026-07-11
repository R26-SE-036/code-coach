public class GenWhileNoUpdateBug107 {
    static void pump(boolean enabled, int quota) {
        while (!enabled) {
            System.out.println(quota);
            quota++;
        }
    }
}
