########################
#file: zbw_tools.py
#Author: zeth willie
#Contact: zethwillie@gmail.com, www.williework.blogspot.com
#Date Modified: 8/17/17
#To Use: type in python window  "import zbw_tools as tools; reload(tools); tools.tools()"
#Notes/Descriptions: some rigging, anim, modeling and shading tools. *** requires zTools folder in a python path.
########################

# todo: add type finder
# todo: maybe add space buffer?
# todo: deformer weights
# todo: refactor all others to use this as much as possible
# todo: drop in all mel scripts deal with sourceing mel scripts from zTools (comet, etc with attribution), brave rabbit
# TODO add some tooltips to buttons
# Todo - add docs to all of these
# todo maybe add shader/uv transfer to rig?
# TODo move the dictionary to resources and pull it from there

from functools import partial
import os
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as om
import zTools.rig.zbw_rig as rig
import zTools.resources.zbw_pipe as pipe
reload(pipe)

widgets = {}

# make sure maya can see and call mel scripts from zTools (where this is called from)
zToolsPath = os.path.dirname(os.path.abspath(__file__))
subpaths = ["", "rig", "resources", "anim", "model", "shaderRender"]
newPaths = []
for p in subpaths:
    thisPath = os.path.join(zToolsPath, p)
    newPaths.append(thisPath)
pipe.add_maya_script_paths(newPaths)


zRigDict = {
    "attr":"import zTools.rig.zbw_attributes as zat; reload(zat); zat.attributes()",
    "snap":"import zTools.rig.zbw_snap as snap; reload(snap), snap.snap()",
    "shpScl":"import zTools.rig.zbw_shapeScale as zss; zss.shapeScale()",
    "selBuf":"import zTools.rig.zbw_selectionBuffer as buf; reload(buf); buf.selectionBuffer()",
    "smIK":"import zTools.rig.zbw_smallIKStretch as zsik; zsik.smallIKStretch()",
    "foll":"import zTools.rig.zbw_makeFollicle as zmf; reload(zmf); zmf.makeFollicle()",
    "ribbon":"import zTools.rig.zbw_ribbon as zrib; reload(zrib); zrib.ribbon()",
    "soft":"import zTools.rig.zbw_softDeformer as zsft; reload(zsft); zsft.softDeformer()",
    "jntRadius":"import zTools.rig.zbw_jointRadius as jntR; jntR.jointRadius()",
    "cmtRename":"mel.eval('cometRename')",
    "trfmBuffer":"import zTools.rig.zbw_transformBuffer as ztbuf; reload(ztbuf); ztbuf.transformBuffer()",
    "crvTools":"import zTools.rig.zbw_curveTools as ctool; reload(ctool); ctool.curveTools()",
    "abSym":"mel.eval('abSymMesh')",
    "cmtJntOrnt":"mel.eval('cometJointOrient')",
    "autoSquash":"import zTools.rig.zbw_autoSquashRig as zAS; reload(zAS); zAS.autoSquashRig()"
}

zAnimDict = {
    "tween":"import zTools.anim.tweenMachine as tm; tm.start()",
    "noise":"import zTools.anim.zbw_animNoise as zAN; reload(zAN); zAN.animNoise()",
    "audio":"import zTools.anim.zbw_audioManager as zAM; reload(zAM); zAM.audioManager()",
    "clean":"import zTools.anim.zbw_cleanKeys as zCK; reload(zCK); zCK.cleanKeys()",
    "dupe":"import zTools.anim.zbw_dupeSwap as zDS; reload(zDS);zDS.dupeSwap()",
    "huddle":"import zTools.anim.zbw_huddle as zH; reload(zH);zH.huddle()",
    "randomSel":"import zTools.anim.zbw_randomSelection as zRS; reload(zRS);zRS.randomSelection()",
    "randomAttr":"import zTools.anim.zbw_randomAttrs as zRA; reload(zRA); zRA.randomAttrs()",
    "clip":"import zTools.anim.zbw_setClipPlanes as zSC; reload(zSC); zSC.setClipPlanes()",
    "tangents":"import zTools.anim.zbw_tangents as zTan; reload(zTan); zTan.tangents()"
}

zModelDict = {
    "extend":"import zTools.model.zbw_polyExtend as zPE; reload(zPE); zPE.polyExtend()",
    "wrinkle":"import zTools.model.zbw_wrinklePoly as zWP; reload(zWP); zWP.wrinklePoly()"
}

zShdDict = {
    "transfer":"import zTools.shaderRender.zbw_shadingTransfer as zST; reload(zST); zST.shadingTransfer()"
}

colors = {'red':13, 'blue':6, 'green':14, 'yellow':17, 'pink':20, 'ltBlue':18, 'brown':10, 'purple':30, 'dkGreen':7}


def tools_UI(*args):
    if cmds.window("toolsWin", exists=True):
        cmds.deleteUI("toolsWin")

    widgets["win"] = cmds.window("toolsWin", t="zbw_tools", w=280, rtf=True, s=True)
    widgets["tab"] = cmds.tabLayout(w=280)
    widgets["rigCLO"] = cmds.columnLayout("RIG", w=280)
    widgets["rigFLO"] = cmds.formLayout(w=280, bgc = (0.1,0.1,0.1))

#controls layout
    widgets["ctrlFLO"] = cmds.formLayout(w=113, h=380, bgc = (0.3,0.3,0.3))
    widgets["ctrlFrLO"] = cmds.frameLayout(l="CONTROLS", w=113, h=380, bv=True, bgc = (0.3,0.3,0.3))
    widgets["ctrlCLO"] = cmds.columnLayout(bgc = (0.3,0.3,0.3))

    widgets["circleBut"] = cmds.button(l="circle", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "circle"))
    widgets["sphereBut"] = cmds.button(l="sphere", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "sphere"))
    widgets["squareBut"] = cmds.button(l="square", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "square"))
    widgets["boxBut"] = cmds.button(l="box", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "box"))
    widgets["lolBut"] = cmds.button(l="lollipop", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "lollipop"))
    widgets["barbellBut"] = cmds.button(l="barbell", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "barbell"))
    widgets["crossBut"] = cmds.button(l="cross", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "cross"))
    widgets["bentXBut"] = cmds.button(l="bent cross", h=20, w=113, bgc=(.7, .7, .5), c = partial(control, "bentCross"))
    widgets["arrowBut"] = cmds.button(l="arrow", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "arrow"))
    widgets["bentArrowBut"] = cmds.button(l="bent arrow", h=20, w=113, bgc=(.7, .7, .5), c = partial(control, "bentArrow"))
    widgets["splitOBut"] = cmds.button(l="split circle", h=20, w=113, bgc=(.7, .7, .5), c = partial(control, "splitCircle"))
    widgets["cylinderBut"] = cmds.button(l="cylinder", h=20, w=113, bgc=(.7, .7, .5), c = partial(control, "cylinder"))
    widgets["starBut"] = cmds.button(l="star", w=113, h=20, bgc=(.7, .7, .5), c = partial(control, "star"))
    widgets["octagonBut"] = cmds.button(l="octagon", h=20, w=113, bgc=(.7, .7, .5), c = partial(control, "octagon"))
    widgets["halfCircBut"] = cmds.button(l="half circle", h=20, w=113, bgc=(.7, .7, .5), c = partial(control, "halfCircle"))
    widgets["crossArrow"] = cmds.button(l="arrow cross", h=20, w=113, bgc=(.7, .7, .5), c = partial(control, "arrowCross"))	
    cmds.separator(h=10, style="none")
    widgets["ctrlAxisRBG"] = cmds.radioButtonGrp(nrb=3, la3=("x", "y", "z"), cw=([1, 33], [2, 33], [3, 33]), cal=([1, "left"], [2, "left"], [3, "left"]), sl=1)

#action layout
    cmds.setParent(widgets["rigFLO"])
    widgets["actionFLO"] = cmds.formLayout(w=150, h=380, bgc = (0.3,0.3,0.3))
    widgets["actionFrLO"] = cmds.frameLayout(l="ACTIONS", w=150, h=380, bv=True, bgc = (0.3,0.3,0.3))
    widgets["actionCLO"] = cmds.columnLayout(bgc = (0.3,0.3,0.3))
    widgets["grpFrzBut"] = cmds.button(l="group freeze selected", w=150, bgc=(.5, .7, .5), c = group_freeze)
    widgets["grpAbvBut"] = cmds.button(l="insert group above ('Grp')", w=150, bgc=(.5, .7, .5), c = insert_group_above)
    widgets["grpCnctBut"] = cmds.button(l="group freeze connect", w=150, bgc=(.5, .7, .5), c = freeze_and_connect)
    widgets["slctHiBut"] = cmds.button(l="select hierarchy", w=150, bgc=(.5, .7, .5), c = select_hi)
    widgets["prntChnBut"] = cmds.button(l="parent chain selected", w=150, bgc=(.5, .7, .5), c = parent_chain)
    widgets["hideShp"] = cmds.button(l="selection toggle shape vis", w=150, bgc=(.5, .7, .5), c=hide_shape)
    widgets["slctCmptBut"] = cmds.button(l="select components", w=150, bgc=(.5, .7, .5), c = select_components)
    widgets["bBox"] = cmds.button(l="bounding box control", w=150, bgc=(.5, .7, .5), c=bBox)	
    widgets["cpSkinWtsBut"] = cmds.button(l="copy skin & weights", w=150, bgc=(.5, .7, .5), c = copy_skinning)
    widgets["remNSBut"] = cmds.button(l="remove all namespaces", w=150, bgc=(.5, .7, .5), c = remove_namespace)
    widgets["cntrLoc"] = cmds.button(l="selection center locator", w=150, bgc=(.5, .7, .5), c = center_locator)
    widgets["addToLat"] = cmds.button(l="add to lattice", w=150, bgc=(.5, .7, .5), c = add_lattice)
#TODO - buttons for jnt radius? a little field (dv = .1?), little button to execute
    # widgets["incrJnt"] = cmds.button(l="decrJntRad .1", w=70, bgc=(.5, .7, .5), c = partial(jnt_radius, "decr"))
    # widgets["decrJnt"] = cmds.button(l="incrJntRad .1", w=70, bgc=(.5, .7, .5), c = parial(jnt_radius, "incr"))

#script Layout
    cmds.setParent(widgets["rigFLO"])
    widgets["zScrptFLO"] = cmds.formLayout(w=280, bgc = (0.3,0.3,0.3))
    widgets["zScrptFrLO"] = cmds.frameLayout(l="SCRIPTS", w=280, bv=True, bgc = (0.3,0.3,0.3))
    cmds.setParent(widgets["zScrptFLO"])	

    widgets["attrBut"] = cmds.button(l="zbw_attrs", w=135, bgc = (.7, .5, .5), c=partial(zAction, zRigDict, "attr"))
    widgets["shpSclBut"] = cmds.button(l="zbw_shapeScale", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                zRigDict, "shpScl"))
    widgets["selBufBut"] = cmds.button(l="zbw_selectionBuffer", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                     zRigDict,
                                                                                                     "selBuf"))
    widgets["snapBut"] = cmds.button(l="zbw_snap", w=135, bgc = (.7, .5, .5), c=partial(zAction, zRigDict, "snap"))
    widgets["smIKBut"] = cmds.button(l="zbw_smallIKStretch", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                  zRigDict, "smIK"))
    widgets["sftDefBut"] = cmds.button(l="zbw_softDeformers", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                   zRigDict, "soft"))
    widgets["follBut"] = cmds.button(l="zbw_makeFollicle", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                zRigDict, "foll"))
    widgets["ribbonBut"] = cmds.button(l="zbw_ribbon", w=135, bgc = (.7, .5, .5), c=partial(zAction, zRigDict,
                                                                                            "ribbon"))
    widgets["jntRadBut"] = cmds.button(l="zbw_jointRadius", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                 zRigDict,
                                                                                                 "jntRadius"))
    widgets["cmtRename"] = cmds.button(l="cometRename", w=135, bgc = (.5, .5, .5), c=partial(zAction,
                                                                                             zRigDict, "cmtRename"))
    widgets["trnBuffer"] = cmds.button(l="zbw_transformBuffer", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                     zRigDict,
                                                                                                     "trfmBuffer"))
    widgets["abSym"] = cmds.button(l="abSymMesh", w=135, bgc = (.5, .5, .5), c=partial(zAction, zRigDict,
                                                                                                  "abSym"))
    widgets["crvTools"] = cmds.button(l="zbw_curveTools", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                               zRigDict, "crvTools"))
    widgets["cmtJntOrnt"] = cmds.button(l="cometJntOrient", w=135, bgc = (.5, .5, .5), c=partial(zAction,
                                                                                              zRigDict, "cmtJntOrnt"))
    widgets["autoSqRig"] = cmds.button(l="zbw_autoSquashRig", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                              zRigDict,
                                                                                                    "autoSquash"))
    # widgets["cmtJntOrnt"] = cmds.button(l="cometJntOrient", w=135, bgc = (.5, .5, .5), c=partial(zAction,
    #                                                                                          zRigDict, "cmtJntOrnt"))
#color layout
    cmds.setParent(widgets["rigFLO"])
    widgets["colorFLO"] = cmds.formLayout(w=280, h=66, bgc = (0.3,0.3,0.3))
    widgets["colorFrLO"] = cmds.frameLayout(l="COLORS", w=280, h=66, bv=True, bgc = (0.3,0.3,0.3))
    widgets["colorRCLO"] = cmds.rowColumnLayout(nc=6)
    #cmds.setParent(widgets["colorFLO"])
    widgets["redCNV"] = cmds.canvas(w=48, h=20, rgb=(1,0,0), pc=partial(changeColor, colors["red"]))
    widgets["blueCNV"] = cmds.canvas(w=48, h=20, rgb=(0,0,1), pc=partial(changeColor, colors["blue"]))
    widgets["greenCNV"] = cmds.canvas(w=48, h=20, rgb=(0,1,0), pc=partial(changeColor, colors["green"]))
    widgets["yellowCNV"] = cmds.canvas(w=48, h=20, rgb=(1,1,0), pc=partial(changeColor, colors["yellow"]))
    widgets["pinkCNV"] = cmds.canvas(w=48, h=20, rgb=(1,.8,.965), pc=partial(changeColor, colors["pink"]))
    widgets["ltBlueCNV"] = cmds.canvas(w=48, h=20, rgb=(.65,.8,1), pc=partial(changeColor, colors["ltBlue"]))
    widgets["brownCNV"] = cmds.canvas(w=48, h=20, rgb=(.5,.275,0), pc=partial(changeColor, colors["brown"]))
    widgets["purpleCNV"] = cmds.canvas(w=48, h=20, rgb=(.33,0,.33), pc=partial(changeColor, colors["purple"]))
    widgets["dkGreenCNV"] = cmds.canvas(w=48, h=20, rgb=(0,.35,0), pc=partial(changeColor, colors["dkGreen"]))
#---------------- add three more colors    

#formlayout stuff
    cmds.formLayout(widgets["rigFLO"], e=True, af=[
        (widgets["ctrlFLO"], "left", 0),
        (widgets["ctrlFLO"], "top", 0), 
        (widgets["actionFLO"], "left", 125),
        (widgets["actionFLO"], "top", 0),
        (widgets["zScrptFLO"], "left", 0),
        (widgets["zScrptFLO"], "top", 457),
        (widgets["colorFLO"], "left", 0),
        (widgets["colorFLO"], "top", 385),				
        ])

    cmds.formLayout(widgets["zScrptFLO"], e=True, af = [
        (widgets["attrBut"], "left", 0),
        (widgets["attrBut"], "top", 25),
        (widgets["selBufBut"], "left", 140),
        (widgets["selBufBut"], "top", 25),
        (widgets["shpSclBut"], "left", 0),
        (widgets["shpSclBut"], "top", 50),
        (widgets["snapBut"], "left", 140),
        (widgets["snapBut"], "top", 50),
        (widgets["smIKBut"], "left", 0),
        (widgets["smIKBut"], "top", 75),
        (widgets["sftDefBut"], "left", 140),
        (widgets["sftDefBut"], "top", 75),
        (widgets["follBut"], "left", 0),
        (widgets["follBut"], "top", 100),
        (widgets["ribbonBut"], "left", 140),
        (widgets["ribbonBut"], "top", 100),	
        (widgets["jntRadBut"], "left", 0),
        (widgets["jntRadBut"], "top", 125),
        (widgets["cmtRename"], "left", 140),
        (widgets["cmtRename"], "top", 125),
        (widgets["trnBuffer"], "left", 0),
        (widgets["trnBuffer"], "top", 150),						
        (widgets["cmtJntOrnt"], "left", 140),
        (widgets["cmtJntOrnt"], "top", 150),
        (widgets["crvTools"], "left", 0),
        (widgets["crvTools"], "top", 175),	
        (widgets["abSym"], "left", 140),
        (widgets["abSym"], "top", 175),
        (widgets["autoSqRig"], "left", 0),
        (widgets["autoSqRig"], "top", 200),
        ])	

    cmds.setParent(widgets["tab"])
    widgets["modelCLO"] = cmds.columnLayout("MODEL", w=280)
    # curve tools, model scripts, add to lattice, select hierarchy, snap selection buffer, transform buffer
    widgets["MaddToLat"] = cmds.button(l="add to lattice", w=135, bgc=(.5, .7, .5), c=add_lattice)
    widgets["extend"] = cmds.button(l="zbw_polyExtend", w=135, bgc = (.7, .5, .5), c=partial(zAction, zModelDict,
                                                                                             "extend"))
    widgets["wrinkle"] = cmds.button(l="zbw_wrinklePoly", w=135, bgc = (.7, .5, .5), c=partial(zAction, zModelDict,
                                                                                             "wrinkle"))
    widgets["McrvTools"] = cmds.button(l="zbw_curveTools", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                               zRigDict, "crvTools"))
    widgets["MtrnBuffer"] = cmds.button(l="zbw_transformBuffer", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                     zRigDict,
                                                                                                     "trfmBuffer"))

    widgets["MrandomSel"] = cmds.button(l="zhw_randomSel", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,
                                                                                             "randomSel"))
    widgets["MselBufBut"] = cmds.button(l="zbw_selectionBuffer", w=135, bgc = (.7, .5, .5), c=partial(zAction,
                                                                                                     zRigDict,
                                                                                                     "selBuf"))
    widgets["MsnapBut"] = cmds.button(l="zbw_snap", w=135, bgc = (.7, .5, .5), c=partial(zAction, zRigDict, "snap"))
    widgets["MabSym"] = cmds.button(l="abSymMesh", w=135, bgc = (.5, .5, .5), c=partial(zAction, zRigDict,
                                                                                                  "abSym"))
    widgets["McmtRename"] = cmds.button(l="cometRename", w=135, bgc = (.5, .5, .5), c=partial(zAction,
                                                                                             zRigDict, "cmtRename"))

    cmds.setParent(widgets["tab"])
    widgets["animCLO"] = cmds.columnLayout("ANIM", w=280)
    widgets["tween"] = cmds.button(l="tween machine", w=135, bgc = (.5, .5, .5), c=partial(zAction, zAnimDict,"tween"))
    widgets["noise"] = cmds.button(l="zbw_animNoise", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,"noise"))
    widgets["audio"] = cmds.button(l="zbw_audioManager", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,
                                                                                             "audio"))
    widgets["clean"] = cmds.button(l="zbw_cleanKeys", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,"clean"))
    widgets["dupe"] = cmds.button(l="zbw_dupeSwap", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,"dupe"))
    widgets["huddle"] = cmds.button(l="zbw_huddle", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,
                                                                                            "huddle"))
    widgets["randomSel"] = cmds.button(l="zhw_randomSel", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,
                                                                                             "randomSel"))
    widgets["randomAttr"] = cmds.button(l="zbw_randomAttr", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,
                                                                                                "randomAttr"))
    widgets["clip"] = cmds.button(l="zbw_setClipPlanes", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,
                                                                                             "clip"))
    widgets["tangents"] = cmds.button(l="zbw_tangents", w=135, bgc = (.7, .5, .5), c=partial(zAction, zAnimDict,
                                                                                                "tangents"))

    cmds.setParent(widgets["tab"])
    widgets["lgtRndCLO"] = cmds.columnLayout("LGTRND", w=280)
    widgets["transfer"] = cmds.button(l="zbw_shadingTransfer", w=135, bgc = (.7, .5, .5), c=partial(zAction, zShdDict,
                                                                                             "transfer"))

    cmds.window(widgets["win"], e=True, rtf=True, w=5, h=5)
    cmds.showWindow(widgets["win"])

##########
# functions
##########

def control(type="none", *args):
    """
    gets the name from the button pushed and the axis from the radio button group
    and creates a control at the origin
    """
    axisRaw = cmds.radioButtonGrp(widgets["ctrlAxisRBG"], q=True, sl=True)
    if axisRaw == 1:
        axis = "x"
    if axisRaw == 2:
        axis = "y"
    if axisRaw == 3:
        axis = "z"				

    rig.createControl(name = "Ctrl", type = type, axis = axis, color = "yellow")


def zAction(dict=None, action=None, *args):
    """
    grabs the action key from the given dictionary and executes that value
    """
    if action and dict:
        x = dict[action]
        print "executing: {}".format(x)
        exec(x)

    else:
        cmds.warning("zbw_tools.zAction: There was a problem with either the key or the dictionary given! (key: {0}, "
                     "action: {1}".format(action, dict))


def jnt_radius(mode=None, *args):
    pass


def remove_namespace(*args):
    """removes namespaces . . . """
# TODO - ----- use the rig function for this
    rem = ["UI", "shared"]
    ns = cmds.namespaceInfo(lon=True, r=True)
    for y in rem:
        ns.remove(y)

    ns.sort(key = lambda a: a.count(":"), reverse=True)
    for n in ns:
        ps = cmds.ls("{}:*".format(n), type="transform")
        for p in ps:
            cmds.rename(p, p.rpartition(":")[2]) 
        cmds.namespace(rm=n)


def add_lattice(*args):
    """
    select lattice then geo to add to the lattice
    """
    sel =  cmds.ls(sl=True)
    lat = sel[0]
    geo = sel[1:]
    rig.addToLattice(lat, geo)


def group_freeze(*args):
    """group freeze an obj"""

    sel = cmds.ls(sl=True, type="transform")

    for obj in sel:
        rig.groupFreeze(obj)


def nameCheck(name):
    if cmds.objExists(name):
        name = "{}_GRP".format(name)
        print name
        nameCheck(name)
    else:
        return(name)


def insert_group_above(*args):
    sel = cmds.ls(sl=True)

    for obj in sel:
        par = cmds.listRelatives(obj, p=True)
        
        grp = cmds.group(em=True, n="{}_Grp".format(obj))
        
        # grp = nameCheck(grp)

        pos = cmds.xform(obj, q=True, ws=True, rp=True)
        rot = cmds.xform(obj, q=True, ws=True, ro=True)
        
        cmds.xform(grp, ws=True, t=pos)
        cmds.xform(grp, ws=True, ro=rot) 
         
        cmds.parent(obj, grp)
        if par:
            cmds.parent(grp, par[0])


def freeze_and_connect(*args):
    sel = cmds.ls(sl=True)

    ctrlOrig = sel[0]

    for x in range(1, len(sel)):
        obj = sel[x]
        ctrl = cmds.duplicate(ctrlOrig, n = "{}Ctrl".format(obj))[0]
        
        pos = cmds.xform(obj, ws=True, q=True, rp=True)
        rot = cmds.xform(obj, ws=True, q=True, ro=True)
        
        grp = cmds.group(em=True, n="{}Grp".format(ctrl))
        
        cmds.parent(ctrl, grp)
        cmds.xform(grp, ws=True, t=pos)
        cmds.xform(grp, ws=True, ro=rot)
        
        cmds.parentConstraint(ctrl, obj)


def parent_chain(*args):
    #parent chain (select objs, child first. WIll parent in order selected)

    sel = cmds.ls(sl=True)
    sizeSel = len(sel)
    for x in range(0, sizeSel-1):
        cmds.parent(sel[x], sel[x+1])


def select_hi(*args):
    cmds.select(hi=True)


def select_components(*args):
    sel = cmds.ls(sl=True)

    if sel:
        
        for obj in sel:
            shape = cmds.listRelatives(obj, s=True)[0]
            
            if cmds.objectType(shape) == "nurbsCurve":
                cmds.select(cmds.ls("{}.cv[*]".format(obj), fl=True))
                
            elif cmds.objectType(shape) == "mesh":
                cmds.select(cmds.ls("{}.vtx[*]".format(obj), fl=True))
            
            else:
                return


def changeColor(color, *args):
    """change shape color of selected objs"""

    sel = cmds.ls(sl=True)

    if sel:
        for obj in sel:
            shapes = cmds.listRelatives(obj, s=True)
            if shapes:
                for shape in shapes:
                    cmds.setAttr("%s.overrideEnabled"%shape, 1)
                    cmds.setAttr("%s.overrideColor"%shape, color)


def copy_skinning(*args):
    """select the orig bound mesh, then the new unbound target mesh and run"""

    sel = cmds.ls(sl=True)
    orig = sel[0]
    target = sel[1]

    #get orig obj joints
    try:
        jnts = cmds.skinCluster(orig, q=True, influence = True)
    except:
        cmds.warning("couldn't get skin weights from {}".format(orig))

    #bind the target with the jnts
    try:
        targetClus = cmds.skinCluster(jnts, target, bindMethod=0, skinMethod=0, normalizeWeights=1, maximumInfluences = 3, obeyMaxInfluences=False, tsb=True)[0]
        print targetClus
    except:
        cmds.warning("couln't bind to {}".format(target))
            
    #get skin clusters
    origClus = mel.eval("findRelatedSkinCluster " + orig)

    #copy skin weights from orig to target
    try:
        cmds.copySkinWeights(ss=origClus, ds=targetClus, noMirror=True, sa="closestPoint", ia="closestJoint")
    except:
        cmds.warning("couldn't copy skin weights from {0} to {1}".format(orig, target))


def center_locator(*args):
    """creates a center loc on the avg position"""

    sel = cmds.ls(sl=True, fl=True)
    if sel:
        ps = []
        for vtx in sel:
            ps.append(cmds.xform(vtx, q=True, ws=True, rp=True))

        # this is cool!
        center = [sum(y)/len(y) for y in zip(*ps)]

        loc = cmds.spaceLocator(name="center_locator")
        cmds.xform(loc, ws=True, t=center)


def hide_shape(*args):
    """hides the shape nodes of the selected objects"""

    sel = cmds.ls(sl=True)
    if sel:
        for obj in sel:
            shp = cmds.listRelatives(obj, shapes = True)
            if shp:
                for s in shp:
                    if cmds.getAttr("{}.visibility".format(s)):
                        cmds.setAttr("{}.visibility".format(s), 0)
                    else:
                        cmds.setAttr("{}.visibility".format(s), 1)


def bBox(*args):
    """creates a control based on the bounding box"""
    sel = cmds.ls(sl=True, type="transform")
    if sel:
        rig.boundingBoxCtrl(sel)

##########
# load function
##########

def tools(*args):
    tools_UI()