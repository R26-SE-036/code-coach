public class ArrayIndexBug014 {
    public boolean getLastStatus(boolean[] flags) {
        return flags[flags.length];
    }
}
